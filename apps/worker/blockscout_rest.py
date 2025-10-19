"""Blockscout REST API client (adapter for when MCP is not available)."""
import asyncio
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BlockscoutRESTClient:
    """
    REST API client for Blockscout explorers.
    
    This is a fallback when MCP server is not available.
    Uses Blockscout API v2 endpoints.
    
    Reference: https://docs.blockscout.com/get-started/integrating-data
    """
    
    def __init__(
        self, 
        api_base_url: str, 
        chain_id: int,
        decimals_cache_path: str = "state/erc20_decimals.json",
        block_ts_cache_path: str = "state/block_ts.json",
        timeout: float = 30.0
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.chain_id = chain_id
        self.timeout = timeout
        self.decimals_cache_path = Path(decimals_cache_path)
        self.block_ts_cache_path = Path(block_ts_cache_path)
        
        # Create cache directories
        self.decimals_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.block_ts_cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load caches
        self.decimals_cache = self._load_cache(self.decimals_cache_path)
        self.block_ts_cache = self._load_cache(self.block_ts_cache_path)
        
        self._client = None  # Lazy initialization per event loop
        self.available_tools = [
            "get_latest_block",
            "get_transactions_by_address",
            "get_logs",
            "get_block_info",
            "get_erc20_decimals",
            "get_erc20_symbol",
        ]
        self.method_map = {
            "get_latest_block": "get_latest_block",
            "get_transactions_by_address": "get_transactions_by_address",
            "get_logs": "get_logs",
            "get_block_info": "get_block_info",
            "get_erc20_decimals": "get_erc20_decimals",
            "get_erc20_symbol": "get_erc20_symbol",
        }
    
    def _load_cache(self, path: Path) -> Dict[str, Any]:
        """Load JSON cache from disk."""
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                logger.warning(f"Failed to load cache from {path}, starting fresh")
        return {}
    
    def _save_cache(self, path: Path, data: Dict[str, Any]):
        """Save JSON cache to disk with fsync."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                f.flush()
                import os
                os.fsync(f.fileno())
        except Exception as e:
            logger.error(f"Failed to save cache to {path}: {e}")
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create httpx client for current event loop."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """Close the httpx client and persist caches."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        
        # Persist caches
        self._save_cache(self.decimals_cache_path, self.decimals_cache)
        self._save_cache(self.block_ts_cache_path, self.block_ts_cache)
    
    async def init_session(self) -> List[str]:
        """Initialize session (no-op for REST API)."""
        logger.info("✓ REST API client initialized (no MCP session needed)")
        logger.info(f"✓ Using Blockscout API: {self.api_base_url}")
        logger.info(f"✓ Discovered tools: {', '.join(sorted(self.method_map.keys()))}")
        return self.available_tools
    
    def has_tool(self, canonical_name: str) -> bool:
        """Check if a tool is available."""
        return canonical_name in self.method_map
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def invoke_or_raise(self, tool_name: str, **kwargs) -> Any:
        """
        Invoke a tool with retry logic.
        
        Raises:
            NotImplementedError: If tool doesn't exist
            Exception: If call fails after retries
        """
        if not self.has_tool(tool_name):
            raise NotImplementedError(f"Tool '{tool_name}' not available. Available: {list(self.method_map.keys())}")
        
        # Redact sensitive args for logging
        safe_args = {k: v for k, v in kwargs.items() if k not in ['api_key', 'token', 'secret']}
        logger.debug(f"Invoking {tool_name} with args: {safe_args}")
        
        try:
            method = getattr(self, tool_name)
            result = await method(**kwargs)
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} calling {tool_name}: {e}")
            raise Exception(f"Tool '{tool_name}' failed with HTTP {e.response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Network error calling {tool_name}: {e}")
            raise Exception(f"Tool '{tool_name}' unreachable: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling {tool_name}: {e}")
            raise
    
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
    
    async def get_block_info(self, block_number: int) -> Dict[str, Any]:
        """
        Get block info with timestamp, using cache.
        
        Reference: https://docs.blockscout.com/about/features/api/rpc-endpoints/block
        """
        # Check cache first
        cache_key = str(block_number)
        if cache_key in self.block_ts_cache:
            return self.block_ts_cache[cache_key]
        
        try:
            url = f"{self.api_base_url}/blocks/{block_number}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Parse timestamp
            timestamp_str = data.get("timestamp", "")
            if timestamp_str:
                try:
                    dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    timestamp = int(dt.timestamp())
                except:
                    timestamp = 0
            else:
                timestamp = 0
            
            block_info = {
                "number": int(data.get("height", block_number)),
                "timestamp": timestamp
            }
            
            # Cache result
            self.block_ts_cache[cache_key] = block_info
            
            return block_info
        except Exception as e:
            logger.warning(f"Failed to fetch block {block_number} info: {e}")
            # Return best guess
            return {"number": block_number, "timestamp": 0}
    
    async def get_erc20_decimals(self, address: str) -> int:
        """
        Get ERC20 token decimals with caching.
        
        Reference: https://docs.blockscout.com/about/features/api/rpc-endpoints/token
        """
        # Check cache
        cache_key = address.lower()
        if cache_key in self.decimals_cache:
            return self.decimals_cache[cache_key]
        
        try:
            url = f"{self.api_base_url}/tokens/{address}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            decimals = int(data.get("decimals", 18))
            
            # Cache result
            self.decimals_cache[cache_key] = decimals
            
            return decimals
        except Exception as e:
            logger.warning(f"Failed to fetch decimals for {address}: {e}, defaulting to 18")
            # Default to 18 and cache it
            self.decimals_cache[cache_key] = 18
            return 18
    
    async def get_erc20_symbol(self, address: str) -> str:
        """
        Get ERC20 token symbol.
        
        Reference: https://docs.blockscout.com/about/features/api/rpc-endpoints/token
        """
        try:
            url = f"{self.api_base_url}/tokens/{address}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            return data.get("symbol", "UNKNOWN")
        except Exception as e:
            logger.warning(f"Failed to fetch symbol for {address}: {e}")
            return "UNKNOWN"


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
        chain_id=settings.CHAIN_ID,
        decimals_cache_path=settings.DECIMALS_CACHE_PATH,
        block_ts_cache_path=settings.BLOCK_TS_CACHE_PATH
    )
    
    return client
