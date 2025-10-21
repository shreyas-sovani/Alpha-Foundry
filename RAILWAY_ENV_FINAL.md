# 🚀 FINAL Railway Environment Variables

## Based on Complete Workspace Analysis

After analyzing your entire workspace including:
- ✅ Autoscout instance (`infra/autoscout/instance.json`)
- ✅ Chainlink price feed integration (`apps/worker/chainlink_price.py`)
- ✅ Settings configuration (`apps/worker/settings.py`)
- ✅ Main worker loop (`apps/worker/run.py`)
- ✅ Demo configuration (`.env.mainnet.recommended`)

---

## 📋 COMPLETE ENVIRONMENT VARIABLES FOR RAILWAY

### Copy and paste ALL of these into Railway's RAW Editor:

```bash
# ============================================================================
# BLOCKSCOUT & AUTOSCOUT CONFIGURATION
# ============================================================================

# Blockscout API - Your Autoscout Instance
BLOCKSCOUT_MCP_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2

# Autoscout Explorer Base URL (from infra/autoscout/instance.json)
AUTOSCOUT_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

# Ethereum Mainnet (from infra/autoscout/instance.json)
CHAIN_ID=1
NETWORK_LABEL=Ethereum Mainnet

# ============================================================================
# DEX POOL CONFIGURATION - Uniswap V3 High-Activity Pools
# ============================================================================

# DEX Type
DEX_TYPE=v3

# USDC/WETH 0.05% fee tier - highest liquidity V3 pool (~$300M+ TVL)
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640

# WETH/USDT 0.05% fee tier - second highest liquidity V3 pool
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6

# Token configuration (optional - pools auto-resolve tokens)
TOKEN0=
TOKEN1=

# ============================================================================
# WORKER BEHAVIOR - HACKATHON OPTIMIZED
# ============================================================================

# Polling & Windows
WORKER_POLL_SECONDS=15
WINDOW_MINUTES=2
MAX_ROWS_PER_ROTATION=1000
PREVIEW_ROWS=8
MCP_INIT_ON_START=true

# HTTP Server Configuration
WORKER_HTTP_HOST=0.0.0.0
WORKER_HTTP_PORT=8787

# Windowing Strategy
WINDOW_STRATEGY=timestamp
BLOCK_LOOKBACK=100
MAX_PAGES_PER_CYCLE=5
EARLY_STOP_MODE=

# ============================================================================
# CHAINLINK PRICE FEED CONFIGURATION
# ============================================================================

# Reference ETH Price (fallback when Chainlink unavailable)
# Chainlink feed for Mainnet: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
# Worker auto-detects this based on CHAIN_ID=1
REFERENCE_ETH_PRICE_USD=2500.0

# ============================================================================
# ACTIVITY VALIDATION & MONITORING
# ============================================================================

# Pool Activity Validation
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300

# ============================================================================
# VISUAL ENHANCEMENTS
# ============================================================================

# Enable emoji markers (🔥 NEW, 💎 WHALE, ⭐ LARGE, ⚡ VOLATILE)
ENABLE_EMOJI_MARKERS=true

# Enable spread/arbitrage alerts
ENABLE_SPREAD_ALERTS=true

# ============================================================================
# ROLLING WINDOW CONFIGURATION
# ============================================================================

# Maximum rows to keep in dexarb_latest.jsonl
ROLLING_WINDOW_SIZE=1000
ROLLING_WINDOW_UNIT=rows

# ============================================================================
# STATE & OUTPUT PATHS (Railway will use /app as working directory)
# ============================================================================

# State files
LAST_BLOCK_STATE_PATH=state/last_block.json
DECIMALS_CACHE_PATH=state/erc20_decimals.json
BLOCK_TS_CACHE_PATH=state/block_ts.json

# Output directory
DATA_OUT_DIR=apps/worker/out

# Output files
PREVIEW_PATH=apps/worker/out/preview.json
METADATA_PATH=apps/worker/out/metadata.json

# ============================================================================
# LOGGING & SCHEMA
# ============================================================================

# Logging level (DEBUG for initial deployment, INFO for production)
LOG_LEVEL=INFO

# Schema version
SCHEMA_VERSION=1.1
```

---

## 🔍 VARIABLE BREAKDOWN BY CATEGORY

### 1. **Autoscout Integration** (from `infra/autoscout/instance.json`)
```bash
BLOCKSCOUT_MCP_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2
AUTOSCOUT_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com
CHAIN_ID=1
```
**Purpose**: Your custom Autoscout instance for Ethereum Mainnet DEX data.

---

### 2. **Chainlink Price Feed** (from `apps/worker/chainlink_price.py`)
```bash
REFERENCE_ETH_PRICE_USD=2500.0
```
**How it works**:
- Worker auto-detects Chainlink feed based on `CHAIN_ID`:
  - Mainnet (1): `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`
  - Sepolia (11155111): `0x694AA1769357215DE4FAC081bf1f309aDC325306`
- Falls back to `REFERENCE_ETH_PRICE_USD` if Chainlink unavailable
- Tries to infer price from recent WETH/USDC swaps as secondary fallback

---

### 3. **DEX Pools** (from `.env.mainnet.recommended`)
```bash
DEX_TYPE=v3
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
```
**Pool Details**:
- **Pool A**: Uniswap V3 USDC/WETH 0.05% (~$300M TVL) - Highest volume
- **Pool B**: Uniswap V3 WETH/USDT 0.05% - Second highest volume

These emit **Swap events directly** (not routers), ensuring clean, high-quality data.

---

### 4. **Worker Performance** (from `DEMO_README.md` optimizations)
```bash
WORKER_POLL_SECONDS=15      # Ultra-fast refresh
WINDOW_MINUTES=2            # Tight time window
PREVIEW_ROWS=8              # Rich preview display
MAX_PAGES_PER_CYCLE=5       # Rate-limit safe
```
**Optimized for**: Live demos with frequent updates and rich data.

---

### 5. **Analytics Features** (from `apps/worker/run.py`)
```bash
ENABLE_EMOJI_MARKERS=true
ENABLE_SPREAD_ALERTS=true
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300
```
**What you get**:
- 🔥 NEW swaps highlighted
- 💎 WHALE trades (>$10k)
- ⭐ LARGE trades (>$1k)
- ⚡ VOLATILE price movements
- 🎯 ARB OPPORTUNITY alerts when spread >0.5%

---

### 6. **State Management** (from `settings.py`)
```bash
LAST_BLOCK_STATE_PATH=state/last_block.json
DECIMALS_CACHE_PATH=state/erc20_decimals.json
BLOCK_TS_CACHE_PATH=state/block_ts.json
DATA_OUT_DIR=apps/worker/out
```
**Purpose**: Persistent caches and checkpoints for resumability.

---

## 🚨 CRITICAL NOTES

### **Why These Specific Pools?**

Your `.env.mainnet.recommended` file specifically chose:
- **V3 pools** (not routers) for direct Swap event emission
- **0.05% fee tier** (highest liquidity)
- **USDC/WETH + WETH/USDT** (most active pairs)

This ensures:
✅ Constant swap activity (swaps every few seconds)
✅ Clean event logs (no router complexity)
✅ Real arbitrage opportunities (cross-pool spread detection)

### **Chainlink Integration**

From `chainlink_price.py`:
- Worker will **attempt** to use Chainlink oracle at `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`
- Currently requires `eth_call` (not yet implemented in REST client)
- **Fallback strategy**:
  1. Try Chainlink (not available yet)
  2. Infer from recent WETH/USDC swaps (median of last 50)
  3. Use `REFERENCE_ETH_PRICE_USD` as final fallback

**Expected log message**:
```
ETH price: $2531.42 (source: inferred_from_swaps)
Chainlink feed address: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
```

### **Autoscout Instance**

Your `infra/autoscout/instance.json` shows you have a **custom Autoscout deployment**:
- **Explorer**: `https://dex-arbitrage-mainnet.cloud.blockscout.com`
- **API**: `https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2`

All transaction links will use this base URL:
```
https://dex-arbitrage-mainnet.cloud.blockscout.com/tx/0x1234...
```

---

## 🎯 HOW TO ADD TO RAILWAY

### Method 1: Bulk Paste (Recommended)

1. Go to Railway Dashboard → Your Project
2. Click **Variables** tab
3. Click **"RAW Editor"** button (top right)
4. **Delete everything** in the editor
5. **Copy the entire block above** (starting from `# ===` to the last variable)
6. **Paste** into RAW Editor
7. Click **"Save"**

### Method 2: Individual Variables

If RAW Editor doesn't work, add these one-by-one:

**Required Core (Minimum)**:
```
BLOCKSCOUT_MCP_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2
AUTOSCOUT_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com
CHAIN_ID=1
DEX_TYPE=v3
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
WORKER_HTTP_HOST=0.0.0.0
WORKER_HTTP_PORT=8787
```

Then add the rest for full functionality.

---

## ✅ EXPECTED BEHAVIOR AFTER DEPLOYMENT

### Successful Startup Logs:
```
======================================================================
🚀 DEX ARBITRAGE WORKER v1.1 - HACKATHON OPTIMIZED
======================================================================
  Network: Ethereum Mainnet (Chain ID: 1)
  BLOCKSCOUT_MCP_BASE: https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2
  AUTOSCOUT_BASE: https://dex-arbitrage-mainnet.cloud.blockscout.com
  DEX_TYPE: v3
  DEX_POOL_A: 0x88e6...640
  DEX_POOL_B: 0x11b8...7F6

  🎯 DEMO OPTIMIZATIONS:
    - Poll interval: 15s (ultra-fast refresh)
    - Time window: 2 min (tight, live data)
    - Preview rows: 8 (rich display)
    - Block lookback: 100 (quick catchup)
    - Max pages/cycle: 5 (rate-limit safe)
    - Emoji markers: ✅
    - Spread alerts: ✅

  📊 STRATEGY:
    - Window: TIMESTAMP
    - ETH Price (est): $2500.0

======================================================================
HTTP ENDPOINTS:
  • http://0.0.0.0:8787/preview
  • http://0.0.0.0:8787/metadata
  • http://0.0.0.0:8787/health
======================================================================
```

### Expected Cycle Output:
```
🔄 CYCLE SUMMARY - HACKATHON DEMO OPTIMIZED
  Network: Ethereum Mainnet (Chain 1)
  Data path: 🎯 LOGS-FIRST (optimal)
  Logs fetched: 47 across 2 pages
  Produced rows: 23
  Rows: 0 -> 23 (delta: +23)
  Early-stop triggered: false

📊 PREVIEW HEADER:
  🚀 7 swaps/2min | Updated 8s ago
  Activity: 3.5 swaps/min
  Spread: 0.42%
  🎯 ARB OPPORTUNITY: PoolA→PoolB +0.42%
  Trend: 📈 +2.15%

✅ VALIDATION: PASS - Dynamic and Useful Data
```

---

## 🌐 TESTING YOUR DEPLOYMENT

Once Railway shows "Deployed":

### 1. Generate Domain
Settings → Networking → **Generate Domain**

### 2. Test Endpoints
```bash
# Health check
curl https://YOUR-APP.up.railway.app/health

# Preview (should show live swaps)
curl https://YOUR-APP.up.railway.app/preview | jq '.header'

# Metadata
curl https://YOUR-APP.up.railway.app/metadata
```

### 3. Expected Preview Response:
```json
{
  "header": {
    "status_emoji": "🚀",
    "activity_ring": "7 swaps/2min | Updated 8s ago",
    "activity_swaps_per_min": 3.5,
    "spread_percent": 0.42,
    "alert": "🎯 ARB OPPORTUNITY: PoolA→PoolB +0.42%"
  },
  "preview_rows": [
    {
      "emoji_marker": "🔥",
      "is_new": true,
      "tx_hash": "0x...",
      "timestamp": 1729440123,
      "token_in_symbol": "WETH",
      "token_out_symbol": "USDC",
      "normalized_price": 2501.23,
      "swap_value_usd": 12500.50,
      "explorer_link": "https://dex-arbitrage-mainnet.cloud.blockscout.com/tx/0x..."
    }
  ],
  "total_rows": 127
}
```

---

## 🎓 VARIABLE EXPLANATION SUMMARY

| Variable | Source | Purpose |
|----------|--------|---------|
| `BLOCKSCOUT_MCP_BASE` | `infra/autoscout/instance.json` | Your custom Autoscout API endpoint |
| `AUTOSCOUT_BASE` | `infra/autoscout/instance.json` | Explorer base URL for tx links |
| `CHAIN_ID` | `infra/autoscout/instance.json` | Network ID (1 = Mainnet) |
| `DEX_POOL_A/B` | `.env.mainnet.recommended` | High-activity Uniswap V3 pools |
| `DEX_TYPE` | `.env.mainnet.recommended` | V3 for direct Swap events |
| `REFERENCE_ETH_PRICE_USD` | `chainlink_price.py` | Fallback when Chainlink unavailable |
| `ENABLE_EMOJI_MARKERS` | `run.py` analytics | Visual enhancements (🔥💎⭐⚡) |
| `ENABLE_SPREAD_ALERTS` | `run.py` analytics | Arbitrage opportunity detection |
| `WORKER_POLL_SECONDS` | `DEMO_README.md` | Ultra-fast refresh for demos |
| `WORKER_HTTP_PORT` | `settings.py` | HTTP server port (8787) |

---

## 🚀 YOU'RE ALL SET!

This configuration uses:
- ✅ Your **custom Autoscout instance** for Mainnet
- ✅ **Chainlink price feed** integration (with smart fallbacks)
- ✅ **Highest-volume Uniswap V3 pools** for constant activity
- ✅ **Demo-optimized settings** (15s refresh, rich analytics)
- ✅ **Full analytics suite** (USD values, MEV warnings, arb alerts)

**Next**: Paste these variables into Railway and watch your worker stream live DEX data! 🎉
