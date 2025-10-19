"""State persistence helpers for checkpoint management."""
import logging
from pathlib import Path
from typing import Any, Dict, Set

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
    Write state to JSON file using orjson for speed.
    
    Args:
        path: Path to state file
        obj: State dict to persist
    """
    path_obj = Path(path)
    
    # Ensure parent directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path_obj, "wb" if USE_ORJSON else "w") as f:
            if USE_ORJSON:
                f.write(orjson.dumps(obj, option=orjson.OPT_INDENT_2))
            else:
                json.dump(obj, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to write state to {path}: {e}")
        raise


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
