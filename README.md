# 🚀 DEX Arbitrage Intelligence Platform

Real-time arbitrage opportunity detection and monetization platform for EVM chains. Continuously monitors DEX pools, detects price discrepancies, and publishes encrypted datasets to **Lighthouse Storage** with automatic cleanup. Built for production deployment on **Railway** with enterprise-grade reliability.

---

## 🪙 **FOR ETHONLINE 2025 JUDGES** - Get Access Tokens

This project uses **DataCoin** (DADC) for token-gated access to premium MEV data.

### 🎯 **How to Get DADC Tokens (Takes 30 seconds):**

**Option 1: Via Etherscan (Easiest)**
1. Visit the faucet: [**Click Here to Claim Tokens**](https://sepolia.etherscan.io/address/0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB#writeContract)
2. Click **"Connect to Web3"** and connect your wallet
3. Find the **"claimTokens"** function
4. Click **"Write"** and confirm the transaction
5. ✅ You'll receive **100 DADC tokens** instantly!

**Option 2: Via Smart Contract**
```javascript
// Faucet Contract: 0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB
const faucet = new ethers.Contract(
  "0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB",
  ["function claimTokens() external"],
  signer
);
await faucet.claimTokens();
```

**Check Your Balance:**
```javascript
// DataCoin: 0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
const dataCoin = new ethers.Contract(
  "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
  ["function balanceOf(address) view returns (uint256)"],
  provider
);
const balance = await dataCoin.balanceOf(yourAddress);
```

**Important Notes:**
- 🌐 Network: **Sepolia Testnet**
- 💧 Each wallet can claim **once** (anti-spam protection)
- 🎫 Minimum balance needed: **1 DADC** token
- ⚡ Claims are instant (no waiting period)

---

## 🎯 What It Does

- **📊 Real-Time Monitoring**: Ingests swap events from Base, Ethereum, Polygon DEX pools every 5 minutes
- **💎 Arbitrage Detection**: Identifies profitable price deltas across DEX pairs using rolling 24h windows
- **🔐 Encrypted Storage**: Publishes datasets to Lighthouse with automatic old file cleanup (maintains single latest file)
- **🔍 Block Explorer Integration**: Every transaction links to Autoscout for deep inspection
- **💬 AI Agent Interface**: ASI:One chat protocol for conversational data access (future)
- **💰 Data Monetization**: Package and sell curated datasets via Lighthouse DataCoin (future)

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    🌐 Railway Platform                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              Python Worker (apps/worker)                │  │
│  │  • Polls DEX events every 5 min via Blockscout MCP     │  │
│  │  • Transforms to JSONL with arbitrage detection        │  │
│  │  • Encrypts & uploads to Lighthouse                    │  │
│  │  • Auto-deletes old files (keeps only latest)          │  │
│  │  • Maintains state: checkpoints, deduplication         │  │
│  └─────────────┬──────────────────────────────────────────┘  │
└────────────────┼──────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│Blockscout│  │Chainlink│  │ Lighthouse   │
│   MCP    │  │  Price  │  │   Storage    │
│  Server  │  │  Feeds  │  │ (Encrypted)  │
└─────────┘  └─────────┘  └──────────────┘
     │            │              │
     ▼            ▼              ▼
┌─────────────────────────────────────┐
│  Base/ETH/Polygon Mainnet (RPC)    │
└─────────────────────────────────────┘
```

**Production Features:**
- ✅ **Auto-Cleanup**: Maintains only 1 file on Lighthouse (deletes old uploads automatically)
- ✅ **Rolling Window**: 24-hour price tracking for accurate arbitrage detection
- ✅ **State Persistence**: Checkpoints, deduplication, price buffers survive restarts
- ✅ **Dual API Failover**: Primary/fallback endpoint switching on errors
- ✅ **HTTP Health Endpoint**: `/health` for Railway monitoring
- ✅ **Multi-Chain**: Base, Ethereum, Polygon support

## 🚀 Quick Start (Railway Deployment)

### Prerequisites
- Railway account ([railway.app](https://railway.app))
- Lighthouse API key ([files.lighthouse.storage](https://files.lighthouse.storage))
- Blockscout API keys for Base, Ethereum, Polygon
- Chainlink price feed contracts (optional, uses fallback if not set)

### Deploy to Railway

1. **Connect Repository**
   ```bash
   railway link
   ```

2. **Set Environment Variables** (in Railway dashboard or CLI)
   ```bash
   # Core Configuration
   BLOCKSCOUT_BASE_URL=https://base.blockscout.com
   BLOCKSCOUT_BASE_API_KEY=your_base_key
   BLOCKSCOUT_ETH_URL=https://eth.blockscout.com
   BLOCKSCOUT_ETH_API_KEY=your_eth_key
   BLOCKSCOUT_POLYGON_URL=https://polygon.blockscout.com
   BLOCKSCOUT_POLYGON_API_KEY=your_polygon_key
   
   # Lighthouse Storage (auto-cleanup enabled)
   LIGHTHOUSE_API_KEY=your_lighthouse_key
   
   # Optional: Chainlink Price Feeds (uses fallback if not set)
   CHAINLINK_ETH_USD=0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
   CHAINLINK_USDC_USD=0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6
   ```

3. **Deploy**
   ```bash
   railway up
   ```

4. **Verify**
   - Check Railway logs for "✅ Lighthouse upload successful"
   - Visit `/health` endpoint to confirm worker is running
   - Check Lighthouse dashboard - should see only 1 encrypted file (auto-cleanup working)

### Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run worker
python apps/worker/run.py

# Test HTTP endpoint
curl http://localhost:8787/health
```

## 📁 Project Structure

```
af_hosted/
├── apps/
│   ├── worker/                    # 🔄 Core ingestion worker
│   │   ├── run.py                 # Main entry point
│   │   ├── blockscout_client.py   # MCP server integration
│   │   ├── chainlink_price.py     # Price feed oracle
│   │   ├── transform.py           # JSONL transformation
│   │   ├── http_server.py         # Health endpoint
│   │   ├── lighthouse_cleanup.py  # Auto file cleanup (NEW)
│   │   └── state/                 # Checkpoints & deduplication
│   └── hosted-agent/              # 💬 Future: ASI:One chat interface
├── infra/
│   └── autoscout/                 # 🔍 Block explorer config
│       └── instance.json          # Explorer URLs
├── scripts/
│   ├── run_worker.sh              # Local development runner
│   └── verify_demo.py             # Demo data generator
├── state/                         # 💾 Persistent state (gitignored)
│   ├── last_block.json
│   ├── dedupe.json
│   ├── price_buffer.json
│   └── block_ts.json
├── nixpacks.toml                  # Railway build configuration
├── Procfile                       # Railway startup command
└── requirements.txt               # Python dependencies
```

## 🔑 Key Features

### ✨ Lighthouse Auto-Cleanup (NEW)
- **Automatic**: Runs after every successful upload
- **Efficient**: Deletes all old files, keeps only latest
- **Smart**: Uses Lighthouse CLI for reliable deletion
- **Fast**: Parallel deletion with progress tracking
- **Production-Ready**: Full error handling & logging

```python
# Happens automatically after each upload
cleanup_lighthouse_storage(
    api_key=LIGHTHOUSE_API_KEY,
    protected_cid="<latest_file_cid>",  # Don't delete this one
    dry_run=False                        # Delete for real
)
# Result: Only 1 file on Lighthouse ✅
```

### 📊 Rolling Window Price Tracking
- 24-hour price history per token
- Accurate min/max/mean calculations
- Automatic expiry of old data
- Persistent across restarts

### 🔄 Dual API Architecture
- Primary endpoint: `api.lighthouse.storage`
- Fallback endpoint: `upload.lighthouse.storage`
- Automatic failover on errors
- SDK upload with REST fallback

### 🎯 Arbitrage Detection
- Real-time price delta calculation
- Multi-DEX comparison (Uniswap, PancakeSwap, SushiSwap)
- Profit opportunity highlighting
- Historical trend analysis

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Platform** | Railway | PaaS deployment with automatic builds |
| **Language** | Python 3.12 | Core worker implementation |
| **Build** | Nixpacks | Automatic dependency detection |
| **Storage** | Lighthouse | Encrypted decentralized file storage |
| **Blockchain** | Blockscout MCP | Chain data access layer |
| **Oracle** | Chainlink | Price feed verification |
| **Explorer** | Autoscout | Transaction inspection UI |

## 📊 Production Status

| Feature | Status | Details |
|---------|--------|---------|
| Worker Deployment | ✅ Live | Running on Railway (asia-southeast1) |
| Lighthouse Upload | ✅ Working | Encrypted JSONL every 5 minutes |
| Auto-Cleanup | ✅ Working | Maintains 1 file only |
| Rolling Window | ✅ Working | 24h price tracking |
| Multi-Chain | ✅ Working | Base + ETH + Polygon |
| HTTP Health | ✅ Working | `/health` endpoint on port 8787 |
| State Persistence | ✅ Working | Survives restarts |
| ASI:One Agent | 🚧 Future | Conversational interface planned |
| DataCoin Sales | 🚧 Future | Dataset monetization planned |

## 🐛 Recent Fixes

### Lighthouse CLI Integration (Oct 2025)
- ✅ Fixed npm global bin PATH in Nix environment
- ✅ Added `[variables]` section to nixpacks.toml for runtime PATH
- ✅ Lighthouse CLI now available to Python subprocess calls
- ✅ Auto-cleanup working in production

### Import Bug Fix (Oct 2025)
- ✅ Fixed missing `from lighthouse_cleanup import cleanup_lighthouse_storage`
- ✅ Added proper error handling for CLI availability
- ✅ Added setup verification on startup

## � Smart Contract Addresses (Sepolia Testnet)

| Contract | Address | Purpose |
|----------|---------|---------|
| **DataCoin (DADC)** | [`0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC`](https://sepolia.etherscan.io/address/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC) | Token-gated access to premium data |
| **Faucet** | [`0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB`](https://sepolia.etherscan.io/address/0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB) | Judges claim tokens here |
| **Liquidity Pool** | [`0x8EF4B1670D382b47DBbF30ebE2Bb15e52Ed2236c`](https://sepolia.etherscan.io/address/0x8EF4B1670D382b47DBbF30ebE2Bb15e52Ed2236c) | DADC/LSDC pool |

**Token Details:**
- Name: DEXArb Data Coin
- Symbol: DADC
- Decimals: 18
- Total Supply: 100,000,000,000 DADC
- Metadata: [ipfs://bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy](https://ipfs.io/ipfs/bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy)

**Deployment Info:**
- Factory: Official 1MB.io factory (`0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990`)
- Lock Asset: 10,000 LSDC
- Creation Tx: [`0x0bf7c4da8b9b05137d08af046d8d360863398f91d747b2d4ac3f5c4bafe235ac`](https://sepolia.etherscan.io/tx/0x0bf7c4da8b9b05137d08af046d8d360863398f91d747b2d4ac3f5c4bafe235ac)

## �📚 Documentation & Resources

### Platform Documentation
- [Railway Platform](https://docs.railway.app/)
- [Nixpacks Build System](https://nixpacks.com/)
- [Lighthouse Storage](https://docs.lighthouse.storage/)
- [Blockscout MCP Server](https://docs.blockscout.com/devs/mcp-server)

### Blockchain & DeFi
- [Base Network](https://docs.base.org/)
- [Chainlink Price Feeds](https://docs.chain.link/data-feeds)
- [Uniswap V3](https://docs.uniswap.org/contracts/v3/overview)
- [1MB.io Platform](https://1mb.io/) - DataCoin creation platform

### Future Integration
- [Agentverse Platform](https://docs.agentverse.ai/)
- [ASI:One Protocol](https://docs.asi1.ai/)
- [Lighthouse DataCoin](https://docs.lighthouse.storage/lighthouse-1/how-to/create-a-datacoin)

## 🤝 Contributing

This is a production system. For contributions:
1. Test locally first with `python apps/worker/run.py`
2. Verify Lighthouse upload works
3. Check auto-cleanup deletes old files
4. Ensure health endpoint responds
5. Submit PR with detailed testing notes

## 📄 License

Proprietary - All Rights Reserved
