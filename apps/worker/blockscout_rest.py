"""Blockscout REST API client (adapter for when MCP is not available)."""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
import httpx

logger = logging.getLogger(__name__)


class BlockscoutRESTClient:
    """
    REST API client for Blockscout explorers.
    
    This is a fallback when MCP server is not available.
    Uses Blockscout API v2 endpoints.
    
    Reference: https://docs.blockscout.com/get-started/integrating-data
    """
    
    def __init__(self, api_base_url: str, chain_id: int, timeout: float = 30.0):
        self.api_base_url = api_base_url.rstrip("/")
        self.chain_id = chain_id
        self.timeout = timeout
        self._client = None  # Lazy initialization per event loop
        self.available_tools = [
            "get_latest_block",
            "get_transactions_by_address",
            "get_logs",
        ]
        self.method_map = {
            "get_latest_block": "get_latest_block",
            "get_transactions_by_address": "get_transactions_by_address",
            "get_logs": "get_logs",
        }
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create httpx client for current event loop."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """Close the httpx client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def init_session(self) -> List[str]:
        """Initialize session (no-op for REST API)."""
        logger.info("✓ REST API client initialized (no MCP session needed)")
        logger.info(f"✓ Using Blockscout API: {self.api_base_url}")
        return self.available_tools
    
    def has_tool(self, canonical_name: str) -> bool:
        """Check if a tool is available."""
        return canonical_name in self.method_map
    
    async def get_latest_block(self) -> Dict[str, Any]:
        """Get the latest block."""
        url = f"{self.api_base_url}/blocks?type=block"
        
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("items", [])
        if not items:
            raise Exception("No blocks returned from API")
        
        latest = items[0]
        
        # Parse timestamp - it comes as ISO string
        timestamp_str = latest.get("timestamp", "")
        if timestamp_str:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                timestamp = int(dt.timestamp())
            except:
                timestamp = 0
        else:
            timestamp = 0
        
        return {
            "number": int(latest["height"]),
            "timestamp": timestamp
        }
    
    async def get_transactions_by_address(
        self,
        address: str,
        age_from: Optional[int] = None,
        age_to: Optional[int] = None,
        methods: Optional[List[str]] = None,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get transactions for an address."""
        url = f"{self.api_base_url}/addresses/{address}/transactions"
        
        params = {}
        if cursor:
            # Blockscout uses pagination params
            params = cursor if isinstance(cursor, dict) else {}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("items", [])
        next_page_params = data.get("next_page_params")
        
        return items, next_page_params
    
    async def get_logs(
        self,
        address: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        topics: Optional[List[Optional[str]]] = None,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get logs for an address."""
        if not address:
            return [], None
        
        url = f"{self.api_base_url}/addresses/{address}/logs"
        
        params = {}
        if cursor:
            params = cursor if isinstance(cursor, dict) else {}
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        items = data.get("items", [])
        next_page_params = data.get("next_page_params")
        
        return items, next_page_params
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def get_rest_client_from_env(settings) -> BlockscoutRESTClient:
    """
    Factory function to create REST API client from settings.
    
    Args:
        settings: Settings instance
    
    Returns:
        BlockscoutRESTClient
    """
    client = BlockscoutRESTClient(
        api_base_url=settings.BLOCKSCOUT_MCP_BASE,
        chain_id=settings.CHAIN_ID
    )
    
    return client
