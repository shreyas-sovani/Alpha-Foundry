# 🚀 DEX Arbitrage Worker - Hackathon Demo Edition

**Live, Dynamic, Actionable DEX Swap Data for Maximum Impact**

This project ingests real-time DEX swap data from Ethereum Mainnet, enriches it with analytics (USD values, MEV warnings, arbitrage opportunities), and serves it via HTTP endpoints optimized for hackathon demos and live dashboards.

---

## ✨ Key Features (Demo-Optimized)

### 🎯 **Live Data**
- **15-second polling** for ultra-fast refresh
- **2-minute time windows** for tight, recent data
- **Mainnet support** with high-activity pools (Uniswap V2/V3 routers)

### 📊 **Rich Analytics**
- **USD value estimates** (via WETH, USDC, USDT detection)
- **MEV warnings** (price deviations >10% from MA)
- **Arbitrage alerts** (cross-pool spread >0.5%)
- **Price trends** (📈/📉 visual indicators)
- **Gas cost tracking** (ETH + USD)

### 🎨 **Visual Enhancements**
- **Emoji markers**: 🔥 NEW, 💎 WHALE, ⭐ LARGE, ⚡ VOLATILE
- **Status indicators**: 🚀 High activity, ✅ Active, 🟡 Stale
- **Activity rings**: "7 swaps/2min | Updated 8s ago"

### 🔍 **Demo Validation**
- **Staleness detection** (warns if data >5 min old)
- **Activity monitoring** (alerts on low swap count)
- **Preview freshness** (ensures dynamic changes between cycles)

---

## 🏃 Quick Start

### **Option 1: Mainnet Demo (Recommended)**

```bash
# 1. Run the quick demo script
./scripts/quick_demo.sh mainnet

# 2. In another terminal, verify live data
curl -s http://localhost:8787/preview | jq '.header'

# 3. Run verification script (after 30s)
python3 scripts/verify_demo.py
```

### **Option 2: Manual Setup**

```bash
# 1. Copy recommended config
cp .env.mainnet.recommended .env

# 2. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/worker/requirements.txt

# 3. Start worker
cd apps/worker
python3 run.py
```

---

## 📡 API Endpoints

### **GET /preview**
Returns enriched preview with latest swaps:

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
      "tx_hash": "0x1234...",
      "timestamp": 1729440123,
      "token_in_symbol": "WETH",
      "token_out_symbol": "USDC",
      "normalized_price": 2501.23,
      "delta_vs_ma": 2.1,
      "delta_vs_prev_row": 0.05,
      "swap_value_usd": 12500.50,
      "value_method": "USDC",
      "mev_warning": "⚠️  Price 12.5% from MA",
      "explorer_link": "https://etherscan.io/tx/0x1234..."
    }
  ],
  "total_rows": 127,
  "last_updated": "2025-10-20T14:55:23Z"
}
```

### **GET /metadata**
Returns dataset metadata:

```json
{
  "schema_version": "1.1",
  "last_updated": "2025-10-20T14:55:23Z",
  "rows": 127,
  "freshness_minutes": 0,
  "format": "jsonl"
}
```

### **GET /health**
Health check endpoint.

---

## ⚙️ Configuration

### **Recommended Settings (Hackathon)**

```bash
# Network
CHAIN_ID=1  # Ethereum Mainnet
NETWORK_LABEL=Ethereum Mainnet
BLOCKSCOUT_MCP_BASE=https://eth.blockscout.com/api/v2

# Active Pools (Uniswap V2 Routers)
DEX_POOL_A=0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
DEX_POOL_B=0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45

# Performance
WORKER_POLL_SECONDS=15  # Ultra-fast refresh
WINDOW_MINUTES=2        # Tight window
PREVIEW_ROWS=8          # Rich display

# Validation
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300

# Visual
ENABLE_EMOJI_MARKERS=true
ENABLE_SPREAD_ALERTS=true
```

### **Alternative Networks**

**Base Mainnet** (cheaper, faster):
```bash
BLOCKSCOUT_MCP_BASE=https://base.blockscout.com/api/v2
CHAIN_ID=8453
NETWORK_LABEL=Base Mainnet
```

**Sepolia Testnet** (testing only):
```bash
BLOCKSCOUT_MCP_BASE=https://eth-sepolia.blockscout.com/api/v2
CHAIN_ID=11155111
NETWORK_LABEL=Ethereum Sepolia
# ⚠️  Warning: Very low activity, not recommended for demo
```

---

## 🔬 Architecture

### **Data Flow**
```
Blockscout API → REST Client → Transform → Enrich → Preview + JSONL
     ↓              ↓             ↓          ↓          ↓
  Latest       Get Logs     Decode    Analytics   HTTP Server
  Block        (events)     Swaps     (USD, MEV)   :8787
```

### **Key Components**

1. **`blockscout_rest.py`**: REST API client with caching
2. **`transform.py`**: Event decoding + normalization
3. **`run.py`**: Main worker loop with enrichment
4. **`state.py`**: Deduplication, price buffers, preview tracking
5. **`http_server.py`**: Read-only HTTP endpoints

### **Caching Strategy**
- **ERC20 decimals**: Persistent JSON cache
- **Block timestamps**: Persistent JSON cache
- **Dedupe tracker**: Rolling 10k tx+log_index pairs
- **Price buffer**: Last 20 prices per pool for MA calculation

---

## 📊 Demo Validation

### **Self-Reflection Questions**

✅ **Are swaps changing every 30s?**
- Run `python3 scripts/verify_demo.py` to check

✅ **Is each preview noticeably different?**
- Look for new tx_hashes, emoji markers, and alerts

✅ **Are signals compelling for judges?**
- USD values, MEV warnings, arb opportunities visible

### **Manual Checks**

```bash
# Check preview freshness
curl -s http://localhost:8787/preview | jq '.header.updated_ago_seconds'
# Should be <60s

# Check activity
curl -s http://localhost:8787/preview | jq '.header.activity_swaps_per_min'
# Should be >0.1 for mainnet

# Check for arb alerts
curl -s http://localhost:8787/preview | jq '.header.alert'
# May show arbitrage opportunities

# Check visual markers
curl -s http://localhost:8787/preview | jq '.preview_rows[].emoji_marker'
# Should see 🔥, ⭐, 💎, etc.
```

---

## 🐛 Troubleshooting

### **Problem: No new swaps**
**Solution**: Switch to mainnet with active pools
```bash
cp .env.mainnet.recommended .env
# Restart worker
```

### **Problem: Stale data (>5 min old)**
**Causes**:
- Pool has no activity → Use mainnet router
- API rate limit → Reduce `MAX_PAGES_PER_CYCLE`
- Network issue → Check Blockscout API status

**Solution**:
```bash
# Check latest block
curl -s https://eth.blockscout.com/api/v2/blocks/latest | jq

# Verify pool activity on Etherscan
# https://etherscan.io/address/0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
```

### **Problem: Verification fails**
Run diagnostics:
```bash
# Check worker logs
tail -f worker.log

# Check state files
ls -lh state/*.json

# Check output
cat apps/worker/out/preview.json | jq '.header'
```

---

## 🎯 Hackathon Tips

### **For Maximum Impact**

1. **Use mainnet**: Testnet data is too sparse
2. **Show live refresh**: Demo with browser auto-refresh on `/preview`
3. **Highlight alerts**: Point out 🎯 ARB OPPORTUNITY banners
4. **Explain MEV**: ⚠️  warnings show price manipulation detection
5. **Dollar values**: USD estimates make data relatable

### **Demo Script**

```bash
# Terminal 1: Start worker
./scripts/quick_demo.sh mainnet

# Terminal 2: Watch live updates
watch -n 5 'curl -s http://localhost:8787/preview | jq ".header"'

# Terminal 3: Show rich data
curl -s http://localhost:8787/preview | jq '.preview_rows[0]'
```

### **Key Talking Points**

- "**Live data** from Ethereum mainnet, refreshing every 15 seconds"
- "**Arbitrage detection**: 🎯 alerts when cross-pool spread >0.5%"
- "**MEV protection**: ⚠️  flags suspicious price movements"
- "**USD conversion**: Instant valuation using stablecoin detection"
- "**Visual UX**: 🔥 for new swaps, 💎 for whale trades"

---

## 📚 References

- [Blockscout API Docs](https://docs.blockscout.com)
- [Autoscout Explorer](https://docs.blockscout.com/using-blockscout/autoscout)
- [Uniswap V2 Contracts](https://docs.uniswap.org/contracts/v2/reference/smart-contracts/v2-deployments)
- [Etherscan](https://etherscan.io)

---

## 📝 License

MIT

---

## 🙏 Acknowledgments

Built with:
- **Blockscout** for blockchain data
- **Uniswap** for DEX infrastructure
- **Python** + `httpx`, `pydantic`, `eth-abi`

**Optimized for Hackathon Demos** 🏆
