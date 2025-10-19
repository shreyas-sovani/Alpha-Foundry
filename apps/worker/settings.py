"""Settings loader using Pydantic BaseSettings."""
import sys
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Worker configuration loaded from environment variables."""
    
    BLOCKSCOUT_MCP_BASE: str
    AUTOSCOUT_BASE: str
    CHAIN_ID: int
    DEX_POOL_A: str
    DEX_POOL_B: str
    WORKER_POLL_SECONDS: int = 300
    LAST_BLOCK_STATE_PATH: str = "state/last_block.json"
    DATA_OUT_DIR: str = "apps/worker/out"
    LOG_LEVEL: str = "INFO"
    WINDOW_MINUTES: int = 5
    MAX_ROWS_PER_ROTATION: int = 1000
    PREVIEW_ROWS: int = 5
    MCP_INIT_ON_START: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_required_fields(self):
        """Validate and exit if required fields are missing."""
        errors = []
        
        if not self.BLOCKSCOUT_MCP_BASE:
            errors.append("BLOCKSCOUT_MCP_BASE is required (e.g., https://mcp.blockscout.com)")
        
        if not self.AUTOSCOUT_BASE:
            errors.append("AUTOSCOUT_BASE is required (your Autoscout explorer URL)")
        
        if not self.CHAIN_ID or self.CHAIN_ID <= 0:
            errors.append("CHAIN_ID is required and must be a positive integer (e.g., 11155111 for Sepolia)")
        
        if not self.DEX_POOL_A and not self.DEX_POOL_B:
            errors.append("At least one pool address (DEX_POOL_A or DEX_POOL_B) must be set")
        
        if errors:
            print("=" * 60)
            print("❌ CONFIGURATION ERROR")
            print("=" * 60)
            for error in errors:
                print(f"  • {error}")
            print("=" * 60)
            print("\nPlease copy .env.example to .env and configure all required variables.")
            print("See: https://docs.blockscout.com/devs/mcp-server")
            sys.exit(1)
    
    def print_redacted(self):
        """Print configuration with sensitive values redacted."""
        print("=" * 60)
        print("Worker Configuration (redacted):")
        print(f"  BLOCKSCOUT_MCP_BASE: {self._redact_url(self.BLOCKSCOUT_MCP_BASE)}")
        print(f"  AUTOSCOUT_BASE: {self._redact_url(self.AUTOSCOUT_BASE)}")
        print(f"  CHAIN_ID: {self.CHAIN_ID}")
        print(f"  DEX_POOL_A: {self._redact_address(self.DEX_POOL_A)}")
        print(f"  DEX_POOL_B: {self._redact_address(self.DEX_POOL_B)}")
        print(f"  WORKER_POLL_SECONDS: {self.WORKER_POLL_SECONDS}")
        print(f"  WINDOW_MINUTES: {self.WINDOW_MINUTES}")
        print(f"  MAX_ROWS_PER_ROTATION: {self.MAX_ROWS_PER_ROTATION}")
        print(f"  PREVIEW_ROWS: {self.PREVIEW_ROWS}")
        print(f"  MCP_INIT_ON_START: {self.MCP_INIT_ON_START}")
        print(f"  LAST_BLOCK_STATE_PATH: {self.LAST_BLOCK_STATE_PATH}")
        print(f"  DATA_OUT_DIR: {self.DATA_OUT_DIR}")
        print(f"  LOG_LEVEL: {self.LOG_LEVEL}")
        print("=" * 60)
    
    @staticmethod
    def _redact_url(url: str) -> str:
        """Redact URL to show only scheme and domain."""
        if not url:
            return "[NOT SET]"
        parts = url.split("://")
        if len(parts) == 2:
            domain = parts[1].split("/")[0]
            return f"{parts[0]}://{domain}/***"
        return "***"
    
    @staticmethod
    def _redact_address(addr: str) -> str:
        """Redact address to show first 6 and last 4 characters."""
        if not addr or len(addr) < 10:
            return "[NOT SET]"
        return f"{addr[:6]}...{addr[-4:]}"
