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
    NETWORK_LABEL: Optional[str] = "Ethereum Mainnet"  # NEW: Human-readable network name
    
    # DEX Configuration
    DEX_TYPE: Literal["v2", "v3"] = "v2"
    DEX_POOL_A: Optional[str] = ""
    DEX_POOL_B: Optional[str] = ""
    TOKEN0: Optional[str] = ""
    TOKEN1: Optional[str] = ""
    
    # Worker Behavior - OPTIMIZED FOR DEMO
    WORKER_POLL_SECONDS: int = 15  # CHANGED: 30->15 for faster refresh
    WORKER_HTTP_HOST: str = "0.0.0.0"
    WORKER_HTTP_PORT: int = 8787
    WINDOW_MINUTES: int = 2  # CHANGED: 5->2 for tighter, more dynamic window
    MAX_ROWS_PER_ROTATION: int = 1000
    PREVIEW_ROWS: int = 8  # CHANGED: 5->8 for richer preview
    LOG_LEVEL: str = "INFO"
    MCP_INIT_ON_START: bool = True
    
    # Windowing Strategy - OPTIMIZED FOR DEMO
    WINDOW_STRATEGY: Literal["timestamp", "block"] = "timestamp"
    BLOCK_LOOKBACK: int = 100  # CHANGED: 500->100 for faster catchup
    MAX_PAGES_PER_CYCLE: int = 5  # CHANGED: 10->5 to avoid rate limits on live mainnet
    
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
    
    # Reference price for USD estimates
    REFERENCE_ETH_PRICE_USD: float = 2500.0
    
    # Rolling Window Configuration - NEW
    ROLLING_WINDOW_SIZE: int = 1000  # Maximum rows to keep in dexarb_latest.jsonl
    ROLLING_WINDOW_UNIT: Literal["rows"] = "rows"  # Future: support "hours", "minutes"
    
    # Pool Activity Validation - NEW
    MIN_SWAPS_PER_CYCLE: int = 1  # Warn if fewer swaps than this
    STALE_THRESHOLD_SECONDS: int = 300  # Alert if no new data in 5 minutes
    
    # Visual Enhancements - NEW
    ENABLE_EMOJI_MARKERS: bool = True  # Add visual markers to new swaps
    ENABLE_SPREAD_ALERTS: bool = True  # Highlight arbitrage opportunities
    
    # Lighthouse Integration - NEW
    LIGHTHOUSE_API_KEY: Optional[str] = ""  # API key for Lighthouse Storage
    LIGHTHOUSE_ENABLE_UPLOAD: bool = False  # Enable automatic upload (default: False to avoid blocking)
    LIGHTHOUSE_UPLOAD_TIMEOUT: int = 60  # Upload timeout in seconds
    
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
        print("=" * 70)
        print(f"🚀 DEX ARBITRAGE WORKER v{self.SCHEMA_VERSION} - HACKATHON OPTIMIZED")
        print("=" * 70)
        print(f"  Network: {self.NETWORK_LABEL or 'Unknown'} (Chain ID: {self.CHAIN_ID})")
        print(f"  BLOCKSCOUT_MCP_BASE: {self._redact_url(self.BLOCKSCOUT_MCP_BASE)}")
        print(f"  AUTOSCOUT_BASE: {self._redact_url(self.AUTOSCOUT_BASE) if self.AUTOSCOUT_BASE else '[NOT SET]'}")
        print(f"  DEX_TYPE: {self.DEX_TYPE}")
        print(f"  DEX_POOL_A: {self._redact_address(self.DEX_POOL_A) if self.DEX_POOL_A else '[NOT SET]'}")
        print(f"  DEX_POOL_B: {self._redact_address(self.DEX_POOL_B) if self.DEX_POOL_B else '[NOT SET]'}")
        print(f"  TOKEN0: {self._redact_address(self.TOKEN0) if self.TOKEN0 else '[NOT SET]'}")
        print(f"  TOKEN1: {self._redact_address(self.TOKEN1) if self.TOKEN1 else '[NOT SET]'}")
        print(f"\n  🎯 DEMO OPTIMIZATIONS:")
        print(f"    - Poll interval: {self.WORKER_POLL_SECONDS}s (ultra-fast refresh)")
        print(f"    - Time window: {self.WINDOW_MINUTES} min (tight, live data)")
        print(f"    - Preview rows: {self.PREVIEW_ROWS} (rich display)")
        print(f"    - Block lookback: {self.BLOCK_LOOKBACK} (quick catchup)")
        print(f"    - Max pages/cycle: {self.MAX_PAGES_PER_CYCLE} (rate-limit safe)")
        print(f"    - Min swaps alert: {self.MIN_SWAPS_PER_CYCLE}")
        print(f"    - Stale threshold: {self.STALE_THRESHOLD_SECONDS}s")
        print(f"    - Rolling window: {self.ROLLING_WINDOW_SIZE} {self.ROLLING_WINDOW_UNIT}")
        print(f"    - Emoji markers: {'✅' if self.ENABLE_EMOJI_MARKERS else '❌'}")
        print(f"    - Spread alerts: {'✅' if self.ENABLE_SPREAD_ALERTS else '❌'}")
        print(f"\n  🔐 LIGHTHOUSE STORAGE:")
        print(f"    - Upload enabled: {'✅' if self.LIGHTHOUSE_ENABLE_UPLOAD else '❌'}")
        print(f"    - API key: {'✅ SET' if self.LIGHTHOUSE_API_KEY else '❌ NOT SET'}")
        print(f"    - Upload timeout: {self.LIGHTHOUSE_UPLOAD_TIMEOUT}s")
        print(f"\n  📊 STRATEGY:")
        print(f"    - Window: {self.WINDOW_STRATEGY.upper()}")
        print(f"    - Early-stop: {self.EARLY_STOP_MODE or self.WINDOW_STRATEGY} (auto)")
        print(f"    - ETH Price (est): ${self.REFERENCE_ETH_PRICE_USD}")
        print(f"\n  💾 PATHS:")
        print(f"    - Decimals cache: {self.DECIMALS_CACHE_PATH}")
        print(f"    - Block→TS cache: {self.BLOCK_TS_CACHE_PATH}")
        print(f"    - State: {self.LAST_BLOCK_STATE_PATH}")
        print(f"    - Preview: {self.PREVIEW_PATH}")
        print("=" * 70)
    
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
