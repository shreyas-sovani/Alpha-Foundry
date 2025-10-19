"""Data transformation utilities for DEX event normalization."""
import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal, InvalidOperation

try:
    from eth_abi import decode
    HAS_ETH_ABI = True
except ImportError:
    HAS_ETH_ABI = False

logger = logging.getLogger(__name__)


def extract_pool_tokens(pool_address: str, dex_type: str, client) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract token0 and token1 addresses from a DEX pool.
    
    Args:
        pool_address: Pool contract address
        dex_type: DEX type ("v2" or "v3")
        client: Blockscout REST client
    
    Returns:
        (token0_address, token1_address) or (None, None) if unavailable
    
    Note: For now, this is a stub that returns None. Full implementation
    would query the pool contract via Blockscout's smart contract read API
    or use eth_call to invoke token0() and token1() view functions.
    
    Workaround: Configure TOKEN0/TOKEN1 in settings and manually set pool_tokens
    cache in state, or use the pool address directly if tokens are known.
    """
    # Stub implementation - return None to skip pool token resolution
    # This prevents errors while we wait for full eth_call integration
    logger.debug(f"Pool token resolution not yet implemented for {pool_address[:8]}...")
    return (None, None)


def normalize_amounts(raw_in: str, raw_out: str, decimals_in: int, decimals_out: int) -> Tuple[str, str]:
    """
    Normalize raw amounts using token decimals.
    
    Args:
        raw_in: Raw input amount (wei)
        raw_out: Raw output amount (wei)
        decimals_in: Input token decimals
        decimals_out: Output token decimals
    
    Returns:
        (normalized_in, normalized_out) as strings with 18 decimal places
    """
    try:
        amt_in = Decimal(str(raw_in)) / Decimal(10 ** decimals_in)
        amt_out = Decimal(str(raw_out)) / Decimal(10 ** decimals_out)
        
        # Return with consistent precision
        return (f"{amt_in:.18f}", f"{amt_out:.18f}")
    
    except (InvalidOperation, ValueError):
        return ("0", "0")


# Common DEX swap event signatures
SWAP_EVENT_SIGNATURES = {
    # Uniswap V2 Swap(address,uint256,uint256,uint256,uint256,address)
    "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": {
        "name": "Swap",
        "types": ["address", "uint256", "uint256", "uint256", "uint256", "address"],
        "indexed": [True, False, False, False, False, True],
    },
    # Uniswap V3 Swap(address,address,int256,int256,uint160,uint128,int24)
    "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67": {
        "name": "Swap",
        "types": ["address", "address", "int256", "int256", "uint160", "uint128", "int24"],
        "indexed": [True, True, False, False, False, False, False],
    },
}


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


def decode_swap_event(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Decode a swap event log using known signatures.
    
    Args:
        log: Raw log entry with topics and data
    
    Returns:
        Decoded event dict or None if not a known swap event
    """
    if not HAS_ETH_ABI:
        logger.debug("eth_abi not available, skipping event decoding")
        return None
    
    topics = log.get("topics") or []
    if not topics:
        return None
    
    topic0 = topics[0] if isinstance(topics[0], str) else None
    if not topic0:
        return None
    
    # Normalize topic0 to lowercase with 0x prefix
    if not topic0.startswith("0x"):
        topic0 = "0x" + topic0
    topic0 = topic0.lower()
    
    signature = SWAP_EVENT_SIGNATURES.get(topic0)
    if not signature:
        logger.debug(f"Unknown event signature: {topic0}")
        return None
    
    try:
        # Extract indexed and non-indexed parameters
        indexed_types = [t for t, idx in zip(signature["types"], signature["indexed"]) if idx]
        non_indexed_types = [t for t, idx in zip(signature["types"], signature["indexed"]) if not idx]
        
        # Decode indexed params from topics (skip topic0)
        indexed_values = []
        for i, typ in enumerate(indexed_types):
            if i + 1 < len(topics):
                topic_data = topics[i + 1]
                if isinstance(topic_data, str):
                    # Remove 0x prefix if present
                    topic_hex = topic_data[2:] if topic_data.startswith("0x") else topic_data
                    topic_bytes = bytes.fromhex(topic_hex)
                    decoded = decode([typ], topic_bytes)[0]
                    indexed_values.append(decoded)
        
        # Decode non-indexed params from data
        data = log.get("data") or "0x"
        if isinstance(data, str):
            data_hex = data[2:] if data.startswith("0x") else data
            if data_hex and non_indexed_types:
                data_bytes = bytes.fromhex(data_hex)
                non_indexed_values = list(decode(non_indexed_types, data_bytes))
            else:
                non_indexed_values = []
        else:
            non_indexed_values = []
        
        # Merge indexed and non-indexed values
        all_values = []
        indexed_idx = 0
        non_indexed_idx = 0
        
        for is_indexed in signature["indexed"]:
            if is_indexed:
                all_values.append(indexed_values[indexed_idx] if indexed_idx < len(indexed_values) else None)
                indexed_idx += 1
            else:
                all_values.append(non_indexed_values[non_indexed_idx] if non_indexed_idx < len(non_indexed_values) else None)
                non_indexed_idx += 1
        
        return {
            "event_name": signature["name"],
            "values": all_values,
            "types": signature["types"],
        }
    
    except Exception as e:
        logger.warning(f"Failed to decode event {topic0}: {e}")
        return None


async def normalize_log_to_swap(
    log: Dict[str, Any],
    autoscout_base: str,
    pool_tokens: Dict[str, Tuple[str, str]],
    client,
    block_number: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Normalize a log entry to a swap row if it's a swap event.
    
    Args:
        log: Raw log entry
        autoscout_base: Autoscout base URL
        pool_tokens: Cache of pool_address -> (token0, token1)
        client: Blockscout REST client for metadata lookups
        block_number: Optional block number override
    
    Returns:
        Normalized swap row with real token addresses, symbols, decimals, or None
    """
    decoded = decode_swap_event(log)
    if not decoded:
        return None
    
    # Extract transaction details
    tx_hash = log.get("transaction_hash") or log.get("transactionHash") or ""
    log_index = log.get("log_index") or log.get("logIndex") or 0
    timestamp = log.get("timestamp") or log.get("block_timestamp") or 0
    
    # Handle address field (may be string or dict with "hash" field)
    address_field = log.get("address") or {}
    if isinstance(address_field, dict):
        pool_id = address_field.get("hash", "")
    else:
        pool_id = address_field
    
    block_num = block_number or log.get("block_number") or log.get("blockNumber") or 0
    
    if isinstance(timestamp, str):
        try:
            from datetime import datetime
            if "T" in timestamp or "-" in timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = int(dt.timestamp())
            else:
                timestamp = int(timestamp)
        except:
            timestamp = 0
    
    # Resolve pool tokens if not cached
    if pool_id not in pool_tokens:
        token0, token1 = extract_pool_tokens(pool_id, "v2", client)
        if token0 and token1:
            pool_tokens[pool_id] = (token0, token1)
        else:
            logger.warning(f"Cannot resolve tokens for pool {pool_id[:8]}...")
            return None
    
    token0, token1 = pool_tokens[pool_id]
    
    # Parse swap event based on signature
    values = decoded["values"]
    
    # For Uniswap V2: (sender, amount0In, amount1In, amount0Out, amount1Out, to)
    # Determine which direction the swap went
    token_in_addr = None
    token_out_addr = None
    amount_in = "0"
    amount_out = "0"
    
    if len(values) >= 5:
        # Check which amounts are non-zero
        amount0_in = int(values[1]) if len(values) > 1 and values[1] else 0
        amount1_in = int(values[2]) if len(values) > 2 and values[2] else 0
        amount0_out = int(values[3]) if len(values) > 3 and values[3] else 0
        amount1_out = int(values[4]) if len(values) > 4 and values[4] else 0
        
        if amount0_in > 0 and amount1_out > 0:
            # Swapping token0 for token1
            amount_in = str(amount0_in)
            amount_out = str(amount1_out)
            token_in_addr = token0
            token_out_addr = token1
        elif amount1_in > 0 and amount0_out > 0:
            # Swapping token1 for token0
            amount_in = str(amount1_in)
            amount_out = str(amount0_out)
            token_in_addr = token1
            token_out_addr = token0
    
    if not token_in_addr or not token_out_addr:
        logger.warning(f"Cannot determine swap direction for tx {tx_hash[:8]}...")
        return None
    
    # Fetch token metadata
    try:
        decimals_in = await client.get_erc20_decimals(token_in_addr)
        decimals_out = await client.get_erc20_decimals(token_out_addr)
        symbol_in = await client.get_erc20_symbol(token_in_addr)
        symbol_out = await client.get_erc20_symbol(token_out_addr)
    except Exception as e:
        logger.warning(f"Failed to fetch token metadata: {e}")
        decimals_in = 18
        decimals_out = 18
        symbol_in = "UNKNOWN"
        symbol_out = "UNKNOWN"
    
    # Normalize amounts
    norm_in, norm_out = normalize_amounts(amount_in, amount_out, decimals_in, decimals_out)
    
    # Compute normalized price
    normalized_price = compute_normalized_price(amount_in, amount_out, decimals_in, decimals_out)
    
    # Fetch block timestamp if missing
    if timestamp == 0 and block_num > 0:
        try:
            block_info = await client.get_block_info(block_num)
            if block_info:
                timestamp = block_info.get("timestamp", 0)
        except Exception as e:
            logger.debug(f"Could not fetch timestamp for block {block_num}: {e}")
    
    explorer_link = f"{autoscout_base.rstrip('/')}/tx/{tx_hash}"
    
    return {
        "timestamp": int(timestamp),
        "block_number": int(block_num),
        "tx_hash": tx_hash,
        "log_index": int(log_index),
        "token_in": token_in_addr,
        "token_in_symbol": symbol_in,
        "token_out": token_out_addr,
        "token_out_symbol": symbol_out,
        "amount_in": amount_in,
        "amount_out": amount_out,
        "amount_in_normalized": norm_in,
        "amount_out_normalized": norm_out,
        "decimals_in": decimals_in,
        "decimals_out": decimals_out,
        "pool_id": pool_id,
        "normalized_price": normalized_price,
        "delta_vs_other_pool": None,
        "explorer_link": explorer_link,
    }
