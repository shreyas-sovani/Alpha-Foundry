# 🎯 QUICK START: Railway Deployment

## ✅ Your Complete Environment Variables Are Ready!

I've analyzed your **entire workspace** including:
- ✅ Autoscout instance configuration (`infra/autoscout/instance.json`)
- ✅ Chainlink price feed integration (`chainlink_price.py`)
- ✅ Worker settings and validation (`settings.py`, `run.py`)
- ✅ Mainnet recommended configuration

---

## 📋 COPY-PASTE THIS INTO RAILWAY

**File**: `railway_env_variables.txt` ← **Use this!**

### Steps:

1. **Open Railway Dashboard** → Your Project → **Variables** tab

2. **Click "RAW Editor"** (button at top right)

3. **Delete everything** in the editor

4. **Copy from `railway_env_variables.txt`** (or copy below):

```
BLOCKSCOUT_MCP_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2
AUTOSCOUT_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com
CHAIN_ID=1
NETWORK_LABEL=Ethereum Mainnet
DEX_TYPE=v3
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
TOKEN0=
TOKEN1=
WORKER_POLL_SECONDS=15
WINDOW_MINUTES=2
MAX_ROWS_PER_ROTATION=1000
PREVIEW_ROWS=8
MCP_INIT_ON_START=true
WORKER_HTTP_HOST=0.0.0.0
WORKER_HTTP_PORT=8787
WINDOW_STRATEGY=timestamp
BLOCK_LOOKBACK=100
MAX_PAGES_PER_CYCLE=5
EARLY_STOP_MODE=
REFERENCE_ETH_PRICE_USD=2500.0
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300
ENABLE_EMOJI_MARKERS=true
ENABLE_SPREAD_ALERTS=true
ROLLING_WINDOW_SIZE=1000
ROLLING_WINDOW_UNIT=rows
LAST_BLOCK_STATE_PATH=state/last_block.json
DECIMALS_CACHE_PATH=state/erc20_decimals.json
BLOCK_TS_CACHE_PATH=state/block_ts.json
DATA_OUT_DIR=apps/worker/out
PREVIEW_PATH=apps/worker/out/preview.json
METADATA_PATH=apps/worker/out/metadata.json
LOG_LEVEL=INFO
SCHEMA_VERSION=1.1
```

5. **Click "Save"** (or "Update Variables")

6. Railway will **automatically redeploy** (~2-3 minutes)

---

## 🔍 WHAT THIS CONFIGURES

### **Your Custom Autoscout Instance**
- **Explorer**: `https://dex-arbitrage-mainnet.cloud.blockscout.com`
- **API**: `https://dex-arbitrage-mainnet.cloud.blockscout.com/api/v2`
- **Chain**: Ethereum Mainnet (Chain ID: 1)

All transaction links will use your Autoscout URL!

### **Chainlink Price Feed Integration**
- **Mainnet Oracle**: `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`
- **Fallback**: Infers price from WETH/USDC swaps
- **Final Fallback**: `$2500.00` (if all else fails)

Worker will log which price source is used.

### **High-Activity Uniswap V3 Pools**
- **Pool A**: `0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640` (USDC/WETH 0.05%)
  - ~$300M+ TVL
  - Swaps every few seconds
  
- **Pool B**: `0x11b815efB8f581194ae79006d24E0d814B7697F6` (WETH/USDT 0.05%)
  - Second highest liquidity
  - Constant activity

### **Demo Optimizations**
- ⚡ **15-second polling** (ultra-fast refresh)
- 📊 **2-minute windows** (tight, recent data)
- 🎨 **Emoji markers** (🔥 NEW, 💎 WHALE, ⭐ LARGE, ⚡ VOLATILE)
- 🎯 **Arbitrage alerts** (when spread >0.5%)
- 💰 **USD value estimates** (via stablecoin detection)

---

## ✅ EXPECTED DEPLOYMENT LOGS

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
    - Emoji markers: ✅
    - Spread alerts: ✅

======================================================================
HTTP ENDPOINTS:
  • http://0.0.0.0:8787/preview
  • http://0.0.0.0:8787/metadata
  • http://0.0.0.0:8787/health
======================================================================

🔄 CYCLE SUMMARY - HACKATHON DEMO OPTIMIZED
  Network: Ethereum Mainnet (Chain 1)
  Data path: 🎯 LOGS-FIRST (optimal)
  Logs fetched: 47 across 2 pages
  Produced rows: 23
  Rows: 0 -> 23 (delta: +23)

📊 PREVIEW HEADER:
  🚀 7 swaps/2min | Updated 8s ago
  Activity: 3.5 swaps/min
  Spread: 0.42%
  🎯 ARB OPPORTUNITY: PoolA→PoolB +0.42%

✅ VALIDATION: PASS - Dynamic and Useful Data
```

---

## 🌐 AFTER DEPLOYMENT SUCCEEDS

### 1. Generate Public URL
- Go to **Settings** tab → **Networking** section
- Click **"Generate Domain"**
- You'll get: `https://your-app-name.up.railway.app`

### 2. Test Endpoints

```bash
# Health check
curl https://your-app-name.up.railway.app/health

# Preview (live swaps with analytics)
curl https://your-app-name.up.railway.app/preview | jq '.header'

# Full preview
curl https://your-app-name.up.railway.app/preview | jq

# Metadata
curl https://your-app-name.up.railway.app/metadata
```

### 3. Expected Response (Preview)

```json
{
  "header": {
    "status_emoji": "🚀",
    "activity_ring": "7 swaps/2min | Updated 8s ago",
    "activity_swaps_per_min": 3.5,
    "spread_percent": 0.42,
    "alert": "🎯 ARB OPPORTUNITY: PoolA→PoolB +0.42%",
    "price_trend": "📈 +2.15%"
  },
  "preview_rows": [
    {
      "emoji_marker": "🔥",
      "is_new": true,
      "tx_hash": "0x1234567890abcdef...",
      "timestamp": 1729440123,
      "token_in_symbol": "WETH",
      "token_out_symbol": "USDC",
      "amount_in_normalized": "5.0",
      "amount_out_normalized": "12501.15",
      "normalized_price": 2500.23,
      "delta_vs_ma": 2.1,
      "swap_value_usd": 12500.50,
      "value_method": "USDC",
      "gas_cost_usd": 15.23,
      "explorer_link": "https://dex-arbitrage-mainnet.cloud.blockscout.com/tx/0x1234..."
    }
  ],
  "total_rows": 127,
  "last_updated": "2025-10-21T07:55:23Z"
}
```

---

## 📚 DOCUMENTATION FILES

For detailed explanations, see:
- **`RAILWAY_ENV_FINAL.md`** - Complete documentation with variable breakdowns
- **`railway_env_variables.txt`** - Simple copy-paste format (what you just used!)
- **`RAILWAY_ENV_SETUP.md`** - Original setup guide (before workspace analysis)

---

## 🎓 KEY FEATURES YOUR CONFIG ENABLES

### ✅ **Your Custom Autoscout**
All explorer links use your instance:
```
https://dex-arbitrage-mainnet.cloud.blockscout.com/tx/0x...
```

### ✅ **Chainlink Integration**
Auto-detects ETH/USD price from oracle:
```
ETH price: $2531.42 (source: inferred_from_swaps)
Chainlink feed address: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
```

### ✅ **Live Mainnet Data**
Streams from highest-volume pools:
- USDC/WETH: ~$300M TVL, swaps every 2-5 seconds
- WETH/USDT: ~$150M TVL, constant activity

### ✅ **Rich Analytics**
Every swap includes:
- 💰 USD value estimates
- ⚡ Price delta vs moving average
- 🎯 Cross-pool arbitrage opportunities
- ⚠️ MEV warnings (abnormal price movements)
- 🔥 Visual markers (NEW, WHALE, LARGE, VOLATILE)

### ✅ **Demo-Ready**
- 15-second refresh (ultra-fast)
- 2-minute windows (tight, recent data)
- 8-row previews (rich display)
- Activity validation (alerts on stale data)

---

## 🚀 YOU'RE DONE!

1. ✅ Paste variables into Railway RAW Editor
2. ✅ Wait ~2-3 minutes for deployment
3. ✅ Generate public domain
4. ✅ Test `/health`, `/preview`, `/metadata` endpoints
5. ✅ Watch live DEX data streaming! 🎉

**Next**: Your worker will start polling Uniswap V3 pools every 15 seconds and serving enriched swap data via HTTP!
