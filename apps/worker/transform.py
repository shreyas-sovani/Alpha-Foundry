"""Data transformation utilities for DEX event normalization."""
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def normalize_tx(tx: Dict[str, Any], autoscout_base: str) -> List[Dict[str, Any]]:
    """
    Normalize a transaction into swap-like rows.
    
    Args:
        tx: Transaction object from MCP
        autoscout_base: Base URL for Autoscout explorer
    
    Returns:
        List of normalized swap event dicts with fields:
        - timestamp (int): Block timestamp
        - tx_hash (str): Transaction hash
        - token_in (str): Input token address
        - token_out (str): Output token address
        - amount_in (str): Input amount (raw)
        - amount_out (str): Output amount (raw)
        - pool_id (str): Pool/router address
        - normalized_price (float | None): Computed price or None
        - delta_vs_other_pool (float | None): Price delta or None
        - explorer_link (str): Autoscout transaction link
    
    Note: For MVP, we extract basic transfer patterns. Full ABI decoding
    requires method signature matching against known DEX patterns.
    
    Reference: https://docs.blockscout.com/using-blockscout/autoscout
    """
    rows = []
    
    # Extract transaction fields with safe .get access
    tx_hash = tx.get("hash") or tx.get("transaction_hash") or ""
    if not tx_hash:
        logger.warning(f"Transaction missing hash field: {list(tx.keys())}")
        return rows
    
    # Timestamp may be in block data or transaction data
    timestamp = tx.get("timestamp") or tx.get("block_timestamp") or 0
    if isinstance(timestamp, str):
        # Parse ISO or UNIX timestamp string
        try:
            from datetime import datetime
            if "T" in timestamp or "-" in timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = int(dt.timestamp())
            else:
                timestamp = int(timestamp)
        except:
            timestamp = 0
    
    # Pool address (to address for DEX router transactions)
    pool_id = tx.get("to") or tx.get("to_address") or ""
    
    # Method name (if decoded)
    method = tx.get("method") or tx.get("function_name") or tx.get("decoded_input", {}).get("method_id", "")
    
    # Check if this looks like a swap transaction
    swap_methods = [
        "swap",
        "swapExactTokensForTokens",
        "swapTokensForExactTokens",
        "swapExactETHForTokens",
        "swapETHForExactTokens",
        "swapExactTokensForETH",
        "swapTokensForExactETH",
    ]
    
    is_swap = any(method.lower().startswith(sm.lower()) for sm in swap_methods)
    
    # For MVP: Create a placeholder row if it looks like a swap
    # In production, decode input data using eth-abi
    if is_swap or not method:
        # Placeholder values - would normally decode from input data
        token_in = "0x0000000000000000000000000000000000000000"
        token_out = "0x0000000000000000000000000000000000000000"
        amount_in = "0"
        amount_out = "0"
        
        # Try to extract from decoded params if available
        decoded = tx.get("decoded_input") or {}
        params = decoded.get("parameters") or decoded.get("params") or []
        
        if params and isinstance(params, list):
            # Common DEX pattern: amountIn, amountOutMin, path, to, deadline
            for i, param in enumerate(params):
                if isinstance(param, dict):
                    name = param.get("name", "").lower()
                    value = param.get("value")
                    
                    if "amountin" in name or name == "amount":
                        amount_in = str(value)
                    elif "amountout" in name:
                        amount_out = str(value)
                    elif "path" in name and isinstance(value, list) and len(value) >= 2:
                        token_in = value[0]
                        token_out = value[-1]
        
        # Build explorer link - Autoscout is a Blockscout instance
        # Transaction pages follow the pattern: {base}/tx/{hash}
        explorer_link = f"{autoscout_base.rstrip('/')}/tx/{tx_hash}"
        
        row = {
            "timestamp": int(timestamp),
            "tx_hash": tx_hash,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "amount_out": amount_out,
            "pool_id": pool_id,
            "normalized_price": None,  # Computed later if reserves available
            "delta_vs_other_pool": None,  # Computed across pools
            "explorer_link": explorer_link,
        }
        
        rows.append(row)
    
    return rows


def compute_price_delta(price_a: float, price_b: float) -> float:
    """
    Compute percentage price difference between two pools.
    
    Args:
        price_a: Price in pool A
        price_b: Price in pool B
    
    Returns:
        Percentage delta: (price_a - price_b) / price_b * 100
        Returns 0.0 if either price is zero or calculation fails.
    
    Note: This is a naive metric for MVP. Production should use
    TWAP or other robust price oracles.
    """
    try:
        if price_a <= 0 or price_b <= 0:
            return 0.0
        
        a = Decimal(str(price_a))
        b = Decimal(str(price_b))
        
        if b == 0:
            return 0.0
        
        delta = (a - b) / b * Decimal("100")
        return float(delta)
    
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return 0.0


def compute_normalized_price(amount_in: str, amount_out: str, decimals_in: int = 18, decimals_out: int = 18) -> Optional[float]:
    """
    Compute normalized price from swap amounts.
    
    Args:
        amount_in: Raw input amount
        amount_out: Raw output amount
        decimals_in: Token decimals for input token
        decimals_out: Token decimals for output token
    
    Returns:
        Normalized price (output per input) or None if invalid
    """
    try:
        if not amount_in or not amount_out:
            return None
        
        amt_in = Decimal(str(amount_in)) / Decimal(10 ** decimals_in)
        amt_out = Decimal(str(amount_out)) / Decimal(10 ** decimals_out)
        
        if amt_in == 0:
            return None
        
        price = amt_out / amt_in
        return float(price)
    
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return None
