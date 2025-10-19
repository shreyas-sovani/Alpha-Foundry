"""State persistence helpers for checkpoint management."""
import logging
from pathlib import Path
from typing import Any, Dict

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
