"""State persistence helpers for checkpoint management."""
import logging
import time
from pathlib import Path
from typing import Any, Dict, Set, List

try:
    import orjson
    USE_ORJSON = True
except ImportError:
    import json
    USE_ORJSON = False

logger = logging.getLogger(__name__)


def read_state(path: str) -> Dict[str, Any]:
    """
    Read state from JSON file.
    
    Args:
        path: Path to state file
    
    Returns:
        State dict, or empty dict if file doesn't exist
    """
    path_obj = Path(path)
    
    if not path_obj.exists():
        return {}
    
    try:
        with open(path_obj, "rb" if USE_ORJSON else "r") as f:
            if USE_ORJSON:
                return orjson.loads(f.read())
            else:
                return json.load(f)
    except (ValueError, IOError) as e:
        logger.warning(f"Failed to read state from {path}: {e}")
        return {}


def write_state(path: str, obj: Dict[str, Any]) -> None:
    """
    Write state to JSON file using orjson for speed with fsync for safety.
    
    Args:
        path: Path to state file
        obj: State dict to persist
    """
    import os
    
    path_obj = Path(path)
    
    # Ensure parent directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path_obj, "wb" if USE_ORJSON else "w") as f:
            if USE_ORJSON:
                f.write(orjson.dumps(obj, option=orjson.OPT_INDENT_2))
            else:
                json.dump(obj, f, indent=2)
            
            # Flush and fsync for crash safety
            f.flush()
            os.fsync(f.fileno())
    except IOError as e:
        logger.error(f"Failed to write state to {path}: {e}")
        raise


class RollingPriceBuffer:
    """Track recent prices per pool for moving average calculation."""
    
    def __init__(self, max_size: int = 20):
        self.buffers: Dict[str, List[Dict[str, Any]]] = {}
        self.max_size = max_size
    
    def add_price(self, pool_id: str, normalized_price: float, timestamp: int):
        """Add a price to the pool's rolling buffer."""
        if pool_id not in self.buffers:
            self.buffers[pool_id] = []
        
        self.buffers[pool_id].append({
            "price": normalized_price,
            "timestamp": timestamp
        })
        
        # Keep only most recent max_size entries
        if len(self.buffers[pool_id]) > self.max_size:
            self.buffers[pool_id] = self.buffers[pool_id][-self.max_size:]
    
    def get_moving_average(self, pool_id: str, window: int = 5) -> float:
        """
        Compute moving average of last N prices.
        
        CRITICAL: Filters out prices that differ by >10x from median to handle
        mixed swap directions (e.g., WETH→USDC vs USDC→WETH in same pool).
        """
        if pool_id not in self.buffers or not self.buffers[pool_id]:
            return 0.0
        
        recent = self.buffers[pool_id][-window:]
        if not recent:
            return 0.0
        
        prices = [entry["price"] for entry in recent]
        
        # CRITICAL FIX: If prices vary widely (>10x), they're likely from
        # different swap directions. Filter to only use prices in the same magnitude.
        if len(prices) > 1:
            # Calculate median price
            sorted_prices = sorted(prices)
            median_idx = len(sorted_prices) // 2
            median_price = sorted_prices[median_idx]
            
            if median_price > 0:
                # Filter: keep only prices within 10x of median
                filtered = [p for p in prices if 0.1 < (p / median_price) < 10]
                
                if filtered:
                    return sum(filtered) / len(filtered)
        
        # Fallback: simple average
        return sum(prices) / len(prices)
    
    def get_swaps_per_minute(self, pool_id: str, minutes: int = 5) -> float:
        """Compute swaps per minute over recent window."""
        if pool_id not in self.buffers or not self.buffers[pool_id]:
            return 0.0
        
        now = int(time.time())
        cutoff = now - (minutes * 60)
        
        recent = [entry for entry in self.buffers[pool_id] if entry["timestamp"] >= cutoff]
        if not recent:
            return 0.0
        
        # Calculate time span
        if len(recent) == 1:
            return 0.0
        
        time_span = recent[-1]["timestamp"] - recent[0]["timestamp"]
        if time_span <= 0:
            return 0.0
        
        return (len(recent) / time_span) * 60.0
    
    def get_latest_price(self, pool_id: str, max_age_seconds: int = 600) -> float:
        """
        Get most recent price if within max_age_seconds.
        
        CRITICAL: Returns 0 if latest price is an outlier (>10x different from
        recent median), which indicates mixed swap directions in buffer.
        """
        import time
        if pool_id not in self.buffers or not self.buffers[pool_id]:
            return 0.0
        
        latest = self.buffers[pool_id][-1]
        now = int(time.time())
        
        if now - latest["timestamp"] > max_age_seconds:
            return 0.0
        
        latest_price = latest["price"]
        
        # CRITICAL FIX: Check if latest price is consistent with recent prices
        # to avoid using prices from opposite swap direction
        if len(self.buffers[pool_id]) >= 3:
            recent_prices = [e["price"] for e in self.buffers[pool_id][-5:]]
            sorted_prices = sorted(recent_prices)
            median_idx = len(sorted_prices) // 2
            median_price = sorted_prices[median_idx]
            
            if median_price > 0:
                price_ratio = latest_price / median_price
                # Reject if latest price is >10x different from median
                if not (0.1 < price_ratio < 10):
                    return 0.0
        
        return latest_price
    
    def prune_by_timestamp(self, cutoff_timestamp: int):
        """
        Remove price entries older than cutoff_timestamp.
        
        Used during rolling window pruning to keep buffer in sync with JSONL window.
        
        Args:
            cutoff_timestamp: Unix timestamp; entries before this are removed
        """
        pruned_count = 0
        for pool_id, entries in list(self.buffers.items()):
            before = len(entries)
            self.buffers[pool_id] = [e for e in entries if e["timestamp"] >= cutoff_timestamp]
            after = len(self.buffers[pool_id])
            pruned_count += (before - after)
            
            # Remove empty pools
            if not self.buffers[pool_id]:
                del self.buffers[pool_id]
        
        if pruned_count > 0:
            logger.debug(f"Pruned {pruned_count} price entries older than ts={cutoff_timestamp}")
    
    def clean_mixed_directions(self) -> int:
        """
        Remove all prices from pools that have mixed swap directions (>100x variance).
        
        Returns:
            Number of pools cleaned
        """
        cleaned_count = 0
        
        for pool_id, entries in list(self.buffers.items()):
            if len(entries) < 2:
                continue
            
            prices = [e["price"] for e in entries]
            min_price = min(prices)
            max_price = max(prices)
            
            # If max/min ratio > 100, we have mixed directions (e.g., 3880 / 0.00025 = 15,520,000)
            if min_price > 0 and (max_price / min_price) > 100:
                logger.info(f"Clearing pool {pool_id[:8]}... with mixed prices (min={min_price:.6f}, max={max_price:.2f})")
                self.buffers[pool_id] = []
                cleaned_count += 1
        
        # Remove empty pools
        self.buffers = {k: v for k, v in self.buffers.items() if v}
        
        return cleaned_count
    
    def save(self, path: str):
        """Persist rolling buffers to disk."""
        write_state(path, {"buffers": self.buffers})
    
    @classmethod
    def load(cls, path: str, max_size: int = 20) -> "RollingPriceBuffer":
        """Load rolling buffers from disk."""
        buffer = cls(max_size)
        state = read_state(path)
        buffer.buffers = state.get("buffers", {})
        logger.info(f"Loaded price buffers: {len(buffer.buffers)} pools")
        return buffer


class DedupeTracker:
    """Track seen tx_hash + log_index pairs to avoid duplicates."""
    
    def __init__(self, max_size: int = 10000):
        self.seen: Set[str] = set()
        self.max_size = max_size
    
    def is_duplicate(self, tx_hash: str, log_index: int) -> bool:
        """Check if this tx+log combination has been seen."""
        key = f"{tx_hash}:{log_index}"
        return key in self.seen
    
    def mark_seen(self, tx_hash: str, log_index: int):
        """Mark this tx+log combination as seen."""
        key = f"{tx_hash}:{log_index}"
        self.seen.add(key)
        
        # Prune if too large (keep most recent)
        if len(self.seen) > self.max_size:
            # Remove oldest 20%
            to_remove = list(self.seen)[:int(self.max_size * 0.2)]
            for k in to_remove:
                self.seen.discard(k)
            logger.debug(f"Pruned dedupe tracker: {len(to_remove)} items removed")
    
    def prune(self, keys_to_remove: Set[str]):
        """
        Remove specific keys from dedupe tracker.
        
        Used during rolling window pruning to free memory for dropped swaps.
        
        Args:
            keys_to_remove: Set of "tx_hash:log_index" keys to remove
        """
        before_count = len(self.seen)
        self.seen -= keys_to_remove
        removed_count = before_count - len(self.seen)
        if removed_count > 0:
            logger.debug(f"Pruned {removed_count} keys from dedupe tracker")
    
    def save(self, path: str):
        """Persist dedupe tracker to disk."""
        write_state(path, {"seen": list(self.seen)})
    
    @classmethod
    def load(cls, path: str, max_size: int = 10000) -> "DedupeTracker":
        """Load dedupe tracker from disk."""
        tracker = cls(max_size)
        state = read_state(path)
        tracker.seen = set(state.get("seen", []))
        logger.info(f"Loaded dedupe tracker: {len(tracker.seen)} entries")
        return tracker


class PreviewStateTracker:
    """Track last preview transaction hashes to bias selection toward new swaps."""
    
    def __init__(self, max_size: int = 10):
        self.last_preview_hashes: Set[str] = set()
        self.max_size = max_size
    
    def update(self, tx_hashes: List[str]):
        """Update with current preview transaction hashes."""
        self.last_preview_hashes = set(tx_hashes[-self.max_size:])
    
    def is_new(self, tx_hash: str) -> bool:
        """Check if this transaction hash was not in last preview."""
        return tx_hash not in self.last_preview_hashes
    
    def save(self, path: str):
        """Persist preview state to disk."""
        write_state(path, {"last_preview_hashes": list(self.last_preview_hashes)})
    
    @classmethod
    def load(cls, path: str, max_size: int = 10) -> "PreviewStateTracker":
        """Load preview state from disk."""
        tracker = cls(max_size)
        state = read_state(path)
        tracker.last_preview_hashes = set(state.get("last_preview_hashes", []))
        logger.info(f"Loaded preview state: {len(tracker.last_preview_hashes)} entries")
        return tracker
