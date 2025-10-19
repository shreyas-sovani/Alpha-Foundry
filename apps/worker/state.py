"""State persistence helpers for checkpoint management."""
import json
import os
from pathlib import Path
from typing import Any, Dict


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
        with open(path_obj, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to read state from {path}: {e}")
        return {}


def write_state(path: str, obj: Dict[str, Any]) -> None:
    """
    Write state to JSON file.
    
    Args:
        path: Path to state file
        obj: State dict to persist
    """
    path_obj = Path(path)
    
    # Ensure parent directory exists
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path_obj, "w") as f:
            json.dump(obj, f, indent=2)
    except IOError as e:
        print(f"Error: Failed to write state to {path}: {e}")
        raise
