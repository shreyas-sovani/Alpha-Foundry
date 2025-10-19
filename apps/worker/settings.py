"""Settings loader using Pydantic BaseSettings."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Worker configuration loaded from environment variables."""
    
    BLOCKSCOUT_MCP_BASE: str
    AUTOSCOUT_BASE: str
    WORKER_POLL_SECONDS: int = 300
    LAST_BLOCK_STATE_PATH: str = "state/last_block.json"
    DATA_OUT_DIR: str = "apps/worker/out"
    LOG_LEVEL: str = "INFO"
    CHAIN_ID: int
    DEX_POOL_A: str
    DEX_POOL_B: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
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
