"""Blockscout MCP-first client for chain data access."""
import httpx
from typing import Optional, Dict, Any, List


class BlockscoutMCPClient:
    """
    Client for interacting with Blockscout via MCP server.
    
    References:
    - https://docs.blockscout.com/devs/mcp-server
    - https://github.com/blockscout/mcp-server
    """
    
    def __init__(self, mcp_base_url: str, chain_id: int):
        self.mcp_base_url = mcp_base_url.rstrip("/")
        self.chain_id = chain_id
        self.client = httpx.Client(timeout=30.0)
    
    def get_latest_block(self) -> int:
        """
        Get the latest block number for the configured chain.
        
        TODO: Implement using Blockscout MCP tool 'get_latest_block' or equivalent.
        Reference: https://docs.blockscout.com/devs/mcp-server
        """
        raise NotImplementedError("TODO: Call MCP tool to get latest block number")
    
    def get_transaction_info(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction details by hash.
        
        Args:
            tx_hash: Transaction hash (0x...)
        
        TODO: Implement using Blockscout MCP tool 'get_transaction' or equivalent.
        Reference: https://docs.blockscout.com/devs/mcp-server
        """
        raise NotImplementedError("TODO: Call MCP tool to get transaction info")
    
    def get_transaction_logs(
        self,
        address: Optional[str] = None,
        topic: Optional[str] = None,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transaction logs (events) filtered by address and/or topic.
        
        Args:
            address: Contract address to filter by
            topic: Event topic (topic0) to filter by
            from_block: Starting block number
            to_block: Ending block number
            cursor: Pagination cursor for next page
        
        Returns:
            Dict with 'items' (list of logs) and optional 'next_cursor'
        
        TODO: Implement using Blockscout MCP tool 'get_logs' or equivalent.
        Reference: https://docs.blockscout.com/devs/mcp-server
        """
        raise NotImplementedError("TODO: Call MCP tool to get transaction logs")
    
    def get_contract_abi(self, address: str) -> List[Dict[str, Any]]:
        """
        Get verified contract ABI.
        
        Args:
            address: Contract address
        
        TODO: Implement using Blockscout MCP tool 'get_contract_abi' or equivalent.
        Reference: https://docs.blockscout.com/devs/mcp-server
        """
        raise NotImplementedError("TODO: Call MCP tool to get contract ABI")
    
    def read_contract(
        self,
        address: str,
        abi: List[Dict[str, Any]],
        function: str,
        args: List[Any]
    ) -> Any:
        """
        Read from a contract (view/pure function call).
        
        Args:
            address: Contract address
            abi: Contract ABI
            function: Function name to call
            args: Function arguments
        
        TODO: Implement using Blockscout MCP tool 'read_contract' or equivalent.
        Reference: https://docs.blockscout.com/devs/mcp-server
        """
        raise NotImplementedError("TODO: Call MCP tool to read contract state")
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
