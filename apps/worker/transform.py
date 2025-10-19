"""Data transformation utilities for DEX event normalization."""
from typing import Dict, Any, Optional
from decimal import Decimal, InvalidOperation


def normalize_swap_event(log: Dict[str, Any], abi_cache: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw swap event log into a standard format.
    
    Args:
        log: Raw log entry from chain
        abi_cache: Cached ABI data for decoding
    
    Returns:
        Normalized swap event dict with keys:
        - timestamp
        - tx_hash
        - token_in
        - token_out
        - amount_in
        - amount_out
        - pool_id
        - normalized_price
    
    TODO: Implement proper ABI decoding and decimal normalization.
    """
    # Placeholder implementation
    return {
        "timestamp": log.get("timestamp", 0),
        "tx_hash": log.get("transaction_hash", ""),
        "token_in": "0x0000000000000000000000000000000000000000",
        "token_out": "0x0000000000000000000000000000000000000000",
        "amount_in": "0",
        "amount_out": "0",
        "pool_id": log.get("address", ""),
        "normalized_price": 0.0,
    }


def compute_price_delta(price_a: float, price_b: float) -> float:
    """
    Compute percentage price difference between two pools.
    
    Args:
        price_a: Price in pool A
        price_b: Price in pool B
    
    Returns:
        Percentage delta (e.g., 2.5 for 2.5% difference)
    
    Safeguards:
    - Returns 0.0 if either price is zero or invalid
    - Uses Decimal for precision
    """
    try:
        if price_a <= 0 or price_b <= 0:
            return 0.0
        
        a = Decimal(str(price_a))
        b = Decimal(str(price_b))
        
        delta = abs(a - b) / min(a, b) * Decimal("100")
        return float(delta)
    
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return 0.0
