# Alchemy Rate Limit Optimization for Autoscout

## Current Issue
Your custom Autoscout instance at `https://dex-arbitrage-mainnet.cloud.blockscout.com` is hitting Alchemy's rate limits:
- **Error:** "Your app has exceeded its compute units per second capacity"
- **Impact:** Indexer lags behind (4+ minutes delay)
- **Cause:** Blockscout's indexer + worker both polling same Alchemy endpoint

## Recommended Solution: Hybrid Architecture

### ✅ Worker Configuration (Deployed)
```bash
# Use public Blockscout API (no rate limits, real-time data)
BLOCKSCOUT_MCP_BASE=https://eth.blockscout.com/api/v2
AUTOSCOUT_BASE=https://eth.blockscout.com

# Custom instance for reference only
CUSTOM_AUTOSCOUT_UI=https://dex-arbitrage-mainnet.cloud.blockscout.com
```

### 🔧 Autoscout Indexer Optimization (Optional)

If you want to keep your custom Autoscout real-time, configure these env vars in your Autoscout deployment:

#### 1. Reduce Polling Frequency
```bash
# Default: 5000ms, increase to reduce API calls
INDEXER_CATCHUP_BLOCKS_BATCH_SIZE=10
INDEXER_CATCHUP_BLOCKS_CONCURRENCY=1
INDEXER_REALTIME_BLOCKS_BATCH_SIZE=1

# Slow down polling (default: immediate)
BLOCK_TRANSFORMER_REALTIME_FETCHER_MAX_CONCURRENCY=1
```

#### 2. Disable Unnecessary Features
```bash
# Skip token transfers if not needed
INDEXER_DISABLE_TOKEN_INSTANCE_FETCHER=true
INDEXER_DISABLE_PENDING_TRANSACTIONS_FETCHER=true

# Skip internal transactions (saves ~40% CU/s)
INDEXER_DISABLE_INTERNAL_TRANSACTIONS_FETCHER=true
```

#### 3. Target Specific Addresses (Most Effective!)
```bash
# Only index your DEX pools (saves 99% of requests!)
INDEXER_MEMORY_LIMIT=1000000
FIRST_BLOCK=20000000  # Start from recent block

# Configure address watchlist (if Blockscout supports it)
INDEXER_ONLY_FETCH_ADDRESSES=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640,0x11b815efB8f581194ae79006d24E0d814B7697F6
```

#### 4. Use Archive Node Fallback
```bash
# Primary: Alchemy
ETHEREUM_JSONRPC_HTTP_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY

# Fallback: Public endpoints (slower but no limits)
ETHEREUM_JSONRPC_FALLBACK_HTTP_URL=https://ethereum-rpc.publicnode.com

# Enable automatic fallback
ETHEREUM_JSONRPC_FALLBACK_ENABLED=true
```

## Alternative Solutions

### Option A: Upgrade Alchemy Plan 💰
- **Free:** 330 CU/s
- **Growth ($49/mo):** 2,000 CU/s (6x increase)
- **Scale (Custom):** Higher limits + dedicated support

### Option B: Use Multiple RPC Providers 🔄
Spread load across providers:
```bash
# Primary: Alchemy (330 CU/s)
# Fallback 1: Infura (100k req/day free)
# Fallback 2: Ankr (500M CU/month free)
# Fallback 3: Public nodes
```

### Option C: Self-Hosted Ethereum Node 🖥️
Run your own Geth/Erigon node:
- **Pros:** No rate limits, full control
- **Cons:** ~2TB storage, high CPU/RAM, maintenance
- **Cost:** $100-200/month cloud VM

## Monitoring Alchemy Usage

Check your Alchemy dashboard:
1. **Dashboard** → Your App → **Metrics**
2. Monitor: "Compute Units per Second"
3. Set up alerts for 80% threshold

## Current Recommendation

**Keep the hybrid setup:**
- ✅ Worker uses **public Blockscout** (real-time, reliable)
- 🔧 Custom Autoscout for **web UI** (4min lag acceptable for exploration)
- 💸 No extra costs

**When to optimize Autoscout:**
- If you need real-time web UI
- If building dashboard that queries custom instance API
- If rate limit errors disrupt operations

## Testing After Changes

1. Check Alchemy dashboard for reduced CU/s usage
2. Monitor Autoscout indexer logs for lag time
3. Verify worker still receives real-time data from public API

---

**Status:** Railway deployment configured to use public Blockscout API ✅
