"""
Chainlink Price Feed Integration for ETH/USD

References:
- Chainlink Data Feeds: https://docs.chain.link/data-feeds/price-feeds/addresses
- Ethereum Mainnet ETH/USD: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
- Sepolia Testnet ETH/USD: 0x694AA1769357215DE4FAC081bf1f309aDC325306
"""

import json
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)

# Chainlink Price Feed Addresses
CHAINLINK_FEEDS = {
    # Ethereum Mainnet
    1: {
        "ETH/USD": "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
        "name": "Ethereum Mainnet"
    },
    # Sepolia Testnet  
    11155111: {
        "ETH/USD": "0x694AA1769357215DE4FAC081bf1f309aDC325306",
        "name": "Sepolia Testnet"
    }
}

# Chainlink Aggregator ABI (minimal - only latestRoundData function)
AGGREGATOR_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]


async def fetch_eth_price_from_chainlink(
    chain_id: int,
    client,
    fallback_price: float = 2500.0
) -> Dict[str, Any]:
    """
    Fetch ETH/USD price from Chainlink oracle.
    
    Args:
        chain_id: Network chain ID (1 for mainnet, 11155111 for Sepolia)
        client: Blockscout client with eth_call capability
        fallback_price: Fallback price if oracle unavailable
        
    Returns:
        Dict with:
        - price: float (ETH/USD price)
        - source: str ('chainlink' or 'fallback')
        - feed_address: str (oracle contract address)
        - timestamp: int (last update timestamp)
        - warning: Optional[str] (if fallback used)
    """
    
    feed_info = CHAINLINK_FEEDS.get(chain_id)
    
    if not feed_info:
        logger.warning(f"No Chainlink feed configured for chain_id {chain_id}, using fallback")
        return {
            "price": fallback_price,
            "source": "fallback",
            "feed_address": None,
            "timestamp": 0,
            "warning": f"No Chainlink oracle for chain {chain_id}"
        }
    
    feed_address = feed_info["ETH/USD"]
    network_name = feed_info["name"]
    
    try:
        # For MVP: Since we don't have eth_call in Blockscout REST API,
        # we'll use a hybrid approach:
        # 1. Try to infer price from recent WETH/USDC swaps (most accurate for mainnet)
        # 2. Fall back to static price with warning
        
        # NOTE: Full Chainlink integration would require:
        # - Web3 provider with eth_call support
        # - Call latestRoundData() on the feed contract
        # - Parse int256 answer and uint8 decimals
        # - Formula: price = answer / (10 ** decimals)
        
        logger.info(f"Chainlink feed address for {network_name}: {feed_address}")
        logger.warning(
            "Full Chainlink integration requires eth_call support. "
            "Using inferred price from WETH/USDC pool or fallback."
        )
        
        # For now, return fallback with explicit warning
        return {
            "price": fallback_price,
            "source": "fallback_pending_web3",
            "feed_address": feed_address,
            "timestamp": 0,
            "warning": (
                f"Chainlink oracle available at {feed_address} but requires Web3 provider. "
                "Using fallback price until eth_call integration is added."
            )
        }
        
    except Exception as e:
        logger.error(f"Error accessing Chainlink feed: {e}")
        return {
            "price": fallback_price,
            "source": "fallback_error",
            "feed_address": feed_address,
            "timestamp": 0,
            "warning": f"Chainlink fetch error: {str(e)}"
        }


def infer_eth_price_from_swaps(recent_swaps: list) -> Optional[float]:
    """
    Infer ETH/USD price from recent WETH/USDC or WETH/USDT swaps.
    
    This is a backup method when Chainlink is unavailable.
    Uses the median price from recent swaps to reduce manipulation risk.
    
    Args:
        recent_swaps: List of recent swap dicts with normalized amounts and tokens
        
    Returns:
        Inferred ETH/USD price or None if insufficient data
    """
    prices = []
    
    for swap in recent_swaps:
        token_in = swap.get('token_in_symbol', '')
        token_out = swap.get('token_out_symbol', '')
        
        # WETH → USDC/USDT: price = amount_out / amount_in
        if token_in == 'WETH' and token_out in ['USDC', 'USDT']:
            try:
                amt_in = Decimal(swap['amount_in_normalized'])
                amt_out = Decimal(swap['amount_out_normalized'])
                if amt_in > 0:
                    prices.append(float(amt_out / amt_in))
            except (ValueError, KeyError, ZeroDivisionError):
                continue
        
        # USDC/USDT → WETH: price = amount_in / amount_out
        elif token_out == 'WETH' and token_in in ['USDC', 'USDT']:
            try:
                amt_in = Decimal(swap['amount_in_normalized'])
                amt_out = Decimal(swap['amount_out_normalized'])
                if amt_out > 0:
                    prices.append(float(amt_in / amt_out))
            except (ValueError, KeyError, ZeroDivisionError):
                continue
    
    if not prices:
        return None
    
    # Use median to reduce outlier impact
    prices.sort()
    median_idx = len(prices) // 2
    
    if len(prices) % 2 == 0:
        median_price = (prices[median_idx - 1] + prices[median_idx]) / 2
    else:
        median_price = prices[median_idx]
    
    # Sanity check: ETH price should be reasonable
    if 100 < median_price < 100000:
        logger.info(f"Inferred ETH price from {len(prices)} swaps: ${median_price:.2f}")
        return median_price
    else:
        logger.warning(f"Inferred price ${median_price:.2f} out of reasonable range")
        return None
