"""Settings loader using Pydantic BaseSettings."""
import sys
from pydantic_settings import BaseSettings
from typing import Optional, Literal


class Settings(BaseSettings):
    """Worker configuration loaded from environment variables."""
    
    # API & Network
    BLOCKSCOUT_MCP_BASE: str
    AUTOSCOUT_BASE: Optional[str] = ""
    CHAIN_ID: int
    
    # DEX Configuration
    DEX_TYPE: Literal["v2", "v3"] = "v2"
    DEX_POOL_A: Optional[str] = ""
    DEX_POOL_B: Optional[str] = ""
    TOKEN0: Optional[str] = ""
    TOKEN1: Optional[str] = ""
    
    # Worker Behavior
    WORKER_POLL_SECONDS: int = 30
    WORKER_HTTP_HOST: str = "0.0.0.0"
    WORKER_HTTP_PORT: int = 8787
    WINDOW_MINUTES: int = 5
    MAX_ROWS_PER_ROTATION: int = 1000
    PREVIEW_ROWS: int = 5
    LOG_LEVEL: str = "INFO"
    MCP_INIT_ON_START: bool = True
    
    # Windowing Strategy
    WINDOW_STRATEGY: Literal["timestamp", "block"] = "timestamp"
    BLOCK_LOOKBACK: int = 500  # For block strategy
    MAX_PAGES_PER_CYCLE: int = 10  # Limit pagination depth
    
    # Early-stop controls (derived from WINDOW_STRATEGY by default)
    EARLY_STOP_MODE: Optional[Literal["block", "timestamp"]] = None  # Auto-match WINDOW_STRATEGY if None
    
    # State & Cache Paths
    LAST_BLOCK_STATE_PATH: str = "state/last_block.json"
    DECIMALS_CACHE_PATH: str = "state/erc20_decimals.json"
    BLOCK_TS_CACHE_PATH: str = "state/block_ts.json"
    DATA_OUT_DIR: str = "apps/worker/out"
    PREVIEW_PATH: str = "apps/worker/out/preview.json"
    METADATA_PATH: str = "apps/worker/out/metadata.json"
    
    # Schema
    SCHEMA_VERSION: str = "1.1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_required_fields(self):
        """Validate and exit if required fields are missing."""
        errors = []
        
        if not self.BLOCKSCOUT_MCP_BASE:
            errors.append("BLOCKSCOUT_MCP_BASE is required (e.g., https://eth-sepolia.blockscout.com/api/v2)")
        
        if not self.CHAIN_ID or self.CHAIN_ID <= 0:
            errors.append("CHAIN_ID is required and must be a positive integer (e.g., 11155111 for Sepolia)")
        
        # Validate pool configuration
        has_pools = self.DEX_POOL_A and self.DEX_POOL_B
        has_tokens = self.TOKEN0 and self.TOKEN1
        
        if not has_pools and not has_tokens:
            errors.append("Either (DEX_POOL_A + DEX_POOL_B) or (TOKEN0 + TOKEN1) must be set for pool resolution")
        
        if self.DEX_TYPE not in ["v2", "v3"]:
            errors.append("DEX_TYPE must be 'v2' or 'v3'")
        
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
        print(f"Worker Configuration v{self.SCHEMA_VERSION}:")
        print(f"  BLOCKSCOUT_MCP_BASE: {self._redact_url(self.BLOCKSCOUT_MCP_BASE)}")
        print(f"  AUTOSCOUT_BASE: {self._redact_url(self.AUTOSCOUT_BASE) if self.AUTOSCOUT_BASE else '[NOT SET]'}")
        print(f"  CHAIN_ID: {self.CHAIN_ID}")
        print(f"  DEX_TYPE: {self.DEX_TYPE}")
        print(f"  DEX_POOL_A: {self._redact_address(self.DEX_POOL_A) if self.DEX_POOL_A else '[NOT SET]'}")
        print(f"  DEX_POOL_B: {self._redact_address(self.DEX_POOL_B) if self.DEX_POOL_B else '[NOT SET]'}")
        print(f"  TOKEN0: {self._redact_address(self.TOKEN0) if self.TOKEN0 else '[NOT SET]'}")
        print(f"  TOKEN1: {self._redact_address(self.TOKEN1) if self.TOKEN1 else '[NOT SET]'}")
        print(f"  WINDOW_STRATEGY: {self.WINDOW_STRATEGY}")
        print(f"  WINDOW_MINUTES: {self.WINDOW_MINUTES}")
        print(f"  BLOCK_LOOKBACK: {self.BLOCK_LOOKBACK}")
        print(f"  MAX_PAGES_PER_CYCLE: {self.MAX_PAGES_PER_CYCLE}")
        print(f"  EARLY_STOP_MODE: {self.EARLY_STOP_MODE or self.WINDOW_STRATEGY} (auto)")
        print(f"  WORKER_POLL_SECONDS: {self.WORKER_POLL_SECONDS}")
        print(f"  WINDOW_MINUTES: {self.WINDOW_MINUTES}")
        print(f"  Cache Paths:")
        print(f"    - Decimals: {self.DECIMALS_CACHE_PATH}")
        print(f"    - Block→TS: {self.BLOCK_TS_CACHE_PATH}")
        print(f"    - State: {self.LAST_BLOCK_STATE_PATH}")
        print(f"    - Preview: {self.PREVIEW_PATH}")
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
