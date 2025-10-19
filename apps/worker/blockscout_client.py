"""Blockscout MCP-first client for chain data access."""
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """MCP-specific error with structured context."""
    def __init__(self, tool_name: str, args: dict, status_code: Optional[int], message: str):
        self.tool_name = tool_name
        self.args = args
        self.status_code = status_code
        self.message = message
        super().__init__(f"MCP tool '{tool_name}' failed (status={status_code}): {message}")


class MCPClient:
    """
    Async client for Blockscout MCP Server with dynamic tool discovery.
    
    References:
    - https://docs.blockscout.com/devs/mcp-server
    - https://github.com/blockscout/mcp-server
    - https://github.com/blockscout/mcp-server-plugin
    """
    
    def __init__(self, base_url: str, chain_id: int, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.chain_id = chain_id
        self.client = httpx.AsyncClient(timeout=timeout)
        self.session_token: Optional[str] = None
        self.available_tools: List[str] = []
        self.method_map: Dict[str, str] = {}  # Canonical name -> actual tool name
    
    async def init_session(self) -> List[str]:
        """
        Initialize MCP session by calling __get_instructions__ tool.
        
        Returns:
            List of available tool names
        
        Reference: MCP server initialization pattern from plugin docs
        """
        logger.info("Initializing MCP session...")
        
        try:
            # Call the initialization tool to discover available tools
            response = await self._call_tool("__get_instructions__", {})
            
            # Extract available tools from response
            # Format may vary; adapt based on actual server response
            if isinstance(response, dict):
                self.available_tools = response.get("tools", [])
                if "session_token" in response:
                    self.session_token = response["session_token"]
                    logger.info(f"Session token acquired: {self.session_token[:16]}...")
            elif isinstance(response, list):
                self.available_tools = response
            
            # Build method map for canonical names
            self._build_method_map()
            
            logger.info(f"✓ MCP session initialized. Available tools: {', '.join(self.available_tools)}")
            logger.info(f"✓ Method map: {self.method_map}")
            return self.available_tools
        
        except Exception as e:
            logger.warning(f"MCP init_session failed (will proceed anyway): {e}")
            # Set default tools based on MCP server documentation
            self.available_tools = [
                "get_latest_block",
                "get_transactions_by_address",
                "get_contract_abi",
                "read_contract",
                "get_logs"
            ]
            self._build_method_map()
            logger.info(f"Using default tool set: {', '.join(self.available_tools)}")
            return self.available_tools
    
    def _build_method_map(self):
        """Build method map from discovered tools to canonical names."""
        # Map variations to canonical names
        tool_aliases = {
            "get_latest_block": ["get_latest_block", "latest_block", "getLatestBlock"],
            "get_transactions_by_address": ["get_transactions_by_address", "get_transactions", "getTransactions"],
            "get_contract_abi": ["get_contract_abi", "get_abi", "getAbi", "contract_abi"],
            "read_contract": ["read_contract", "readContract", "call_contract"],
            "get_logs": ["get_logs", "getLogs", "get_transaction_logs", "logs"],
            "get_token_info": ["get_token_info", "getTokenInfo", "token_info"],
        }
        
        for canonical, aliases in tool_aliases.items():
            for alias in aliases:
                if alias in self.available_tools:
                    self.method_map[canonical] = alias
                    break
        
        logger.debug(f"Built method map: {self.method_map}")
    
    def has_tool(self, canonical_name: str) -> bool:
        """Check if a tool is available by canonical name."""
        return canonical_name in self.method_map
    
    async def invoke_or_raise(self, canonical_name: str, params: Dict[str, Any]) -> Any:
        """
        Invoke a tool by canonical name or raise NotImplementedError.
        
        Args:
            canonical_name: Canonical tool name (e.g., 'get_logs')
            params: Tool parameters
        
        Returns:
            Tool response
        
        Raises:
            NotImplementedError: If tool is not available
        """
        if not self.has_tool(canonical_name):
            available = ", ".join(sorted(self.method_map.keys()))
            raise NotImplementedError(
                f"Tool '{canonical_name}' not available in MCP server. "
                f"Available tools: {available}. "
                f"See: https://docs.blockscout.com/devs/mcp-server"
            )
        
        actual_tool = self.method_map[canonical_name]
        logger.debug(f"Invoking {canonical_name} -> {actual_tool}")
        return await self._call_tool(actual_tool, params)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
        reraise=True
    )
    async def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Call an MCP tool via HTTP POST.
        
        Args:
            tool_name: Name of the MCP tool
            params: Tool parameters
        
        Returns:
            Tool response (parsed JSON)
        
        Raises:
            MCPError: On tool invocation failure
        """
        url = f"{self.base_url}/{tool_name}"
        
        headers = {"Content-Type": "application/json"}
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
        
        try:
            response = await self.client.post(url, json=params, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                # Retry on 5xx errors
                logger.warning(f"Server error calling {tool_name}: {e.response.status_code}")
                raise
            else:
                # Client errors are not retried
                error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
                raise MCPError(tool_name, params, e.response.status_code, error_detail)
        
        except httpx.TimeoutException as e:
            logger.warning(f"Timeout calling {tool_name}")
            raise MCPError(tool_name, params, None, f"Request timeout: {e}")
        
        except Exception as e:
            raise MCPError(tool_name, params, None, str(e))
    
    async def get_latest_block(self) -> Dict[str, Any]:
        """
        Get the latest block number and timestamp.
        
        Returns:
            Dict with keys: 'number' (int), 'timestamp' (int)
        
        Raises:
            MCPError: If required fields are missing
        
        Reference: https://github.com/blockscout/mcp-server-plugin
        """
        logger.debug(f"Fetching latest block for chain {self.chain_id}")
        
        response = await self._call_tool("get_latest_block", {"chain_id": self.chain_id})
        
        # Validate required fields
        if not isinstance(response, dict):
            raise MCPError("get_latest_block", {"chain_id": self.chain_id}, None, 
                          f"Expected dict response, got {type(response)}")
        
        number = response.get("number") or response.get("block_number") or response.get("height")
        timestamp = response.get("timestamp") or response.get("block_timestamp")
        
        if number is None:
            raise MCPError("get_latest_block", {"chain_id": self.chain_id}, None,
                          f"Response missing 'number' field: {list(response.keys())}")
        
        if timestamp is None:
            raise MCPError("get_latest_block", {"chain_id": self.chain_id}, None,
                          f"Response missing 'timestamp' field: {list(response.keys())}")
        
        return {
            "number": int(number),
            "timestamp": int(timestamp)
        }
    
    async def get_transactions_by_address(
        self,
        address: str,
        age_from: Optional[int] = None,
        age_to: Optional[int] = None,
        methods: Optional[List[str]] = None,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get transactions for an address with optional filtering and pagination.
        
        Args:
            address: Contract address
            age_from: Start timestamp (UNIX seconds) - optional
            age_to: End timestamp (UNIX seconds) - optional
            methods: List of method names to filter by - optional
            cursor: Pagination cursor - optional
        
        Returns:
            Tuple of (transactions list, next_cursor or None)
        
        Reference: https://github.com/blockscout/mcp-server-plugin
        """
        params = {
            "chain_id": self.chain_id,
            "address": address
        }
        
        if age_from is not None:
            params["age_from"] = age_from
        if age_to is not None:
            params["age_to"] = age_to
        if methods:
            params["methods"] = methods
        if cursor:
            params["cursor"] = cursor
        
        logger.debug(f"Fetching transactions for {address[:10]}... with params: {params}")
        
        response = await self._call_tool("get_transactions_by_address", params)
        
        # Handle different response formats
        if isinstance(response, dict):
            items = response.get("items") or response.get("transactions") or response.get("result", [])
            next_cursor = response.get("next_cursor") or response.get("next_page_params")
        elif isinstance(response, list):
            items = response
            next_cursor = None
        else:
            raise MCPError("get_transactions_by_address", params, None,
                          f"Unexpected response type: {type(response)}")
        
        logger.debug(f"Fetched {len(items)} transactions, next_cursor={next_cursor}")
        
        return items, next_cursor
    
    async def get_contract_abi(self, address: str) -> Dict[str, Any]:
        """
        Get verified contract ABI.
        
        Args:
            address: Contract address
        
        Returns:
            ABI dict/list
        
        Reference: https://github.com/blockscout/mcp-server-plugin
        """
        params = {
            "chain_id": self.chain_id,
            "address": address
        }
        
        logger.debug(f"Fetching contract ABI for {address}")
        
        response = await self._call_tool("get_contract_abi", params)
        
        # ABI might be nested in response
        if isinstance(response, dict) and "abi" in response:
            return response["abi"]
        
        return response
    
    async def read_contract(
        self,
        address: str,
        abi: Dict[str, Any],
        function: str,
        args: List[Any]
    ) -> Any:
        """
        Read from a contract (view/pure function call).
        
        Args:
            address: Contract address
            abi: Contract ABI
            function: Function name
            args: Function arguments
        
        Returns:
            Function return value
        
        Note: This tool may not be exposed by all MCP servers.
        Reference: https://docs.blockscout.com/devs/mcp-server
        """
        try:
            params = {
                "chain_id": self.chain_id,
                "address": address,
                "abi": abi,
                "function": function,
                "args": args
            }
            
            logger.debug(f"Reading contract {address} function {function}")
            
            return await self.invoke_or_raise("read_contract", params)
        
        except NotImplementedError as e:
            logger.warning(str(e))
            raise
    
    async def get_logs(
        self,
        address: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        topics: Optional[List[Optional[str]]] = None,
        cursor: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get logs (events) with optional filtering.
        
        Args:
            address: Contract address to filter by
            from_block: Starting block number
            to_block: Ending block number
            topics: List of topics (topic0, topic1, ...) - None for wildcard
            cursor: Pagination cursor
        
        Returns:
            Tuple of (logs list, next_cursor or None)
        
        Reference: https://github.com/blockscout/mcp-server-plugin
        """
        params = {
            "chain_id": self.chain_id
        }
        
        if address:
            params["address"] = address
        if from_block is not None:
            params["from_block"] = from_block
        if to_block is not None:
            params["to_block"] = to_block
        if topics:
            params["topics"] = topics
        if cursor:
            params["cursor"] = cursor
        
        logger.debug(f"Fetching logs for address={address}, blocks={from_block}-{to_block}")
        
        try:
            response = await self.invoke_or_raise("get_logs", params)
        except NotImplementedError:
            logger.warning("get_logs tool not available, falling back to transaction-based approach")
            return [], None
        
        # Handle different response formats
        if isinstance(response, dict):
            items = response.get("items") or response.get("logs") or response.get("result", [])
            next_cursor = response.get("next_cursor") or response.get("next_page_params")
        elif isinstance(response, list):
            items = response
            next_cursor = None
        else:
            items = []
            next_cursor = None
        
        logger.debug(f"Fetched {len(items)} logs, next_cursor={next_cursor}")
        
        return items, next_cursor
    
    async def get_token_info(self, address: str) -> Dict[str, Any]:
        """
        Get ERC20 token information (name, symbol, decimals).
        
        Args:
            address: Token contract address
        
        Returns:
            Dict with token info (decimals, symbol, name)
        
        Note: Falls back to contract reads if tool not available.
        """
        try:
            params = {
                "chain_id": self.chain_id,
                "address": address
            }
            
            response = await self.invoke_or_raise("get_token_info", params)
            return response
        
        except NotImplementedError:
            # Fallback: read contract directly
            logger.debug(f"get_token_info not available, reading contract {address}")
            
            # Standard ERC20 ABI subset
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            ]
            
            try:
                decimals = await self.read_contract(address, erc20_abi, "decimals", [])
                symbol = await self.read_contract(address, erc20_abi, "symbol", [])
                name = await self.read_contract(address, erc20_abi, "name", [])
                
                return {
                    "decimals": int(decimals) if decimals else 18,
                    "symbol": symbol if symbol else "UNKNOWN",
                    "name": name if name else "Unknown Token"
                }
            except Exception as e:
                logger.warning(f"Failed to read token info for {address}: {e}")
                return {"decimals": 18, "symbol": "UNKNOWN", "name": "Unknown Token"}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def get_mcp_client_from_env(settings) -> MCPClient:
    """
    Factory function to create MCP client from settings.
    
    Args:
        settings: Settings instance
    
    Returns:
        MCPClient (not yet initialized - call init_session in async context)
    
    Reference: https://docs.blockscout.com/devs/mcp-server
    """
    client = MCPClient(
        base_url=settings.BLOCKSCOUT_MCP_BASE,
        chain_id=settings.CHAIN_ID
    )
    
    return client
