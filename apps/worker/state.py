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
        """Compute moving average of last N prices."""
        if pool_id not in self.buffers or not self.buffers[pool_id]:
            return 0.0
        
        recent = self.buffers[pool_id][-window:]
        if not recent:
            return 0.0
        
        prices = [entry["price"] for entry in recent]
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
        """Get most recent price if within max_age_seconds."""
        import time
        if pool_id not in self.buffers or not self.buffers[pool_id]:
            return 0.0
        
        latest = self.buffers[pool_id][-1]
        now = int(time.time())
        
        if now - latest["timestamp"] > max_age_seconds:
            return 0.0
        
        return latest["price"]
    
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
