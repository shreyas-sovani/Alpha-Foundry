<div align="center">

<img src="https://github.com/user-attachments/assets/YOUR_UPLOADED_IMAGE_ID" alt="DADC Logo" width="200"/>

# DEXArb Intelligence Platform

**Real-time MEV opportunities, encrypted on-chain, unlocked with tokens.**

[![ETHOnline 2025](https://img.shields.io/badge/ETHOnline-2025-blue.svg)](https://ethglobal.com/events/ethonline2025)
[![Lighthouse](https://img.shields.io/badge/Lighthouse-Encrypted-green.svg)](https://lighthouse.storage)
[![Live on Railway](https://img.shields.io/badge/Railway-Live-success.svg)](https://railway.app)
[![Sepolia](https://img.shields.io/badge/Network-Sepolia-orange.svg)](https://sepolia.etherscan.io)

[🎯 Try Demo](https://dexarb-data-unlock.vercel.app) • [📜 Contracts](https://sepolia.etherscan.io/address/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC) • [🔥 Get Tokens](https://sepolia.etherscan.io/address/0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB#writeContract)

</div>

---

## What This Actually Does

You're a trader looking for arbitrage opportunities across DEX pools. The data is valuable, but you don't want bots scraping it for free. 

This platform:
1. **Monitors DEX swaps** on Ethereum mainnet (Uniswap V3 USDC/WETH pool)
2. **Detects price deltas** that signal arbitrage opportunities
3. **Encrypts everything** using Lighthouse's native encryption
4. **Gates access** with ERC20 tokens - 1 DADC = 1 decrypt
5. **Burns tokens** when you unlock data, creating real scarcity

Think of it as Bloomberg Terminal data, but encrypted on IPFS and unlocked with crypto tokens. Each decrypt costs 1 DADC token (destroyed forever), so 100 tokens = exactly 100 uses.

---

## 🎫 For ETHOnline Judges

**Get access in 30 seconds:**

1. **Claim tokens** → [Open Faucet](https://sepolia.etherscan.io/address/0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB#writeContract)
2. **Connect wallet** → Click "Connect to Web3"
3. **Call `claimTokens()`** → Get 100 DADC instantly
4. **Visit app** → [dexarb-data-unlock.vercel.app](https://dexarb-data-unlock.vercel.app)
5. **Unlock data** → Burns 1 DADC, shows arbitrage opportunities

**Network:** Sepolia Testnet  
**Cost:** 1 DADC per decrypt (burned to 0xdead)  
**Claim limit:** Once per wallet

---

## How It Works

### Backend (Railway)
```
Python Worker
├── Polls Uniswap V3 swaps every 15 seconds (Blockscout API)
├── Calculates arbitrage spreads (token price deltas)
├── Packages as JSONL with timestamps
├── Encrypts with Lighthouse SDK
├── Sets access control: balanceOf(DADC) >= 1 token
└── Auto-cleans old files (keeps only latest)
```

**Key File:** `apps/worker/lighthouse_native_encryption.py`
- Uses Lighthouse's Kavach encryption (not custom AES)
- Signs auth messages with eth-account
- Applies ERC20 access control via SDK
- Uploads to IPFS with distributed key shards

### Frontend (Vercel)
```
Next.js App
├── Connects MetaMask wallet
├── Checks DADC balance → Shows "X decrypts available"
├── User clicks unlock → Burns 1 DADC to 0xdead
├── Signs decryption request → Lighthouse checks new balance
├── Lighthouse grants access → Downloads encrypted file
└── Decrypts locally → Shows arbitrage data
```

**Key File:** `frontend/app/page.tsx`
- Implements `burnTokenForAccess()` function
- Transfers 1 DADC to burn address before each decrypt
- Uses Lighthouse SDK for decryption
- Updates UI to show remaining decrypts

### Smart Contracts (Sepolia)
```
DataCoin (ERC20)
├── Symbol: DADC
├── Supply: 100 billion
├── Created via 1MB.io factory
└── Used for access control

DataCoinFaucet
├── Gives 100 DADC per wallet
├── One-time claim (anti-spam)
└── Instant minting
```

**Deployment:** Created through official 1MB.io factory with 10,000 LSDC lock

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    � User Browser                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         Next.js Frontend (Vercel)                     │  │
│  │  • Connect wallet                                     │  │
│  │  • Burn 1 DADC → 0xdead                              │  │
│  │  • Sign decrypt request                               │  │
│  │  • Download + decrypt locally                         │  │
│  └───────────┬───────────────────────────────────────────┘  │
└──────────────┼──────────────────────────────────────────────┘
               │
               ├──────────► Sepolia Testnet
               │             └── DataCoin.balanceOf() check
               │
               ├──────────► Lighthouse Storage
               │             ├── Check access control
               │             ├── Distribute key shards
               │             └── Serve encrypted CID
               │
┌──────────────┼──────────────────────────────────────────────┐
│              ▼                                               │
│      Python Worker (Railway)                                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │  1. Poll Blockscout API (Uniswap V3 swaps)         │     │
│  │  2. Transform to JSONL (arbitrage detection)       │     │
│  │  3. Encrypt with Lighthouse native SDK             │     │
│  │  4. Apply ERC20 gating (DADC balance >= 1)         │     │
│  │  5. Upload to IPFS (distributed key shards)        │     │
│  │  6. Cleanup old files (keep only latest)           │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
               │
               ├──────────► Ethereum Mainnet RPC
               │             └── Uniswap V3 swap events
               │
               └──────────► Lighthouse API
                             └── Upload encrypted files
```

---

## Token Economics (The Cool Part)

**Problem:** How do you monetize data without letting bots scrape it once and share forever?

**Solution:** Burn tokens on every access.

```
User Journey:
1. Claim 100 DADC from faucet → Balance: 100 DADC
2. Unlock data (burn 1 DADC) → Balance: 99 DADC
3. Unlock again (burn 1 DADC) → Balance: 98 DADC
...
100. Last unlock → Balance: 0 DADC (no more access)
```

**Why it works:**
- Lighthouse checks `balanceOf(userAddress) >= 1 DADC` before each decrypt
- Frontend voluntarily burns 1 DADC before requesting access
- User's balance decreases → Lighthouse naturally denies access when balance hits 0
- No backend burn logic needed (Lighthouse is read-only)
- Creates real scarcity (deflationary model)

**Live burn transactions:** [View on Etherscan](https://sepolia.etherscan.io/address/0x000000000000000000000000000000000000dEaD)

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Next.js 14 + ethers.js v6 | React for UI, ethers for wallet interactions |
| **Encryption** | Lighthouse SDK v0.3.3 | Native Kavach encryption with BLS threshold crypto |
| **Backend** | Python 3.12 + aiohttp | Async worker for high-throughput swap ingestion |
| **Blockchain Data** | Blockscout MCP Server | Structured API for Uniswap V3 swap events |
| **Smart Contracts** | Solidity 0.8.20 | ERC20 (DataCoin) + Faucet on Sepolia |
| **Deployment** | Railway + Vercel | Backend on Railway, frontend on Vercel |
| **State** | JSON files | Checkpoints, deduplication, price buffers |

---

## Project Structure

```
af_hosted/
├── apps/
│   └── worker/                         # Backend (Railway)
│       ├── run.py                      # Main loop: fetch → transform → encrypt → upload
│       ├── lighthouse_native_encryption.py  # Lighthouse SDK wrapper
│       ├── blockscout_client.py        # Blockscout MCP integration
│       ├── transform.py                # DEX event → arbitrage JSONL
│       ├── http_server.py              # Health endpoint
│       └── settings.py                 # Config from env vars
│
├── frontend/                           # Frontend (Vercel)
│   ├── app/
│   │   ├── page.tsx                    # Main unlock page (burn + decrypt)
│   │   ├── layout.tsx                  # Next.js layout
│   │   └── globals.css                 # Tailwind styles
│   ├── next.config.js                  # Next.js config
│   └── package.json                    # npm dependencies
│
├── contracts/
│   └── DataCoinFaucet.sol              # One-time claim faucet
│
├── scripts/
│   ├── createDEXArbDataCoin.js         # 1MB.io factory deployment
│   ├── deployFaucet.js                 # Faucet deployment
│   └── verify_lighthouse_protection.py # Test access control
│
├── state/                              # Worker state (gitignored)
│   ├── last_block.json                 # Last processed block
│   ├── dedupe.json                     # Prevent duplicate swaps
│   └── price_buffer.json               # 24h price rolling window
│
├── requirements.txt                    # Python deps
├── package.json                        # Root npm deps (DataCoin creation)
├── nixpacks.toml                       # Railway build config
└── Procfile                            # Railway start command
```

---

## Smart Contracts

### DataCoin (DADC)
```solidity
Address: 0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
Network: Sepolia Testnet
Standard: ERC20 (1MB.io DataCoin)
Supply: 100,000,000,000 DADC (100 billion)
Decimals: 18
```

**Deployment:**
- Created via official 1MB.io factory
- Locked 10,000 LSDC (Lighthouse Sepolia Data Coin)
- 99% supply available for minting
- 1% in Uniswap liquidity pool

[📜 View on Etherscan](https://sepolia.etherscan.io/address/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC)

### DataCoinFaucet
```solidity
Address: 0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB
Function: claimTokens() → Mints 100 DADC
Limit: One claim per address
```

[📜 View on Etherscan](https://sepolia.etherscan.io/address/0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB)

---

## Running Locally

### Prerequisites
- Node.js 18+ (for Lighthouse SDK)
- Python 3.12+
- MetaMask wallet on Sepolia

### Backend (Worker)

```bash
cd apps/worker

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Lighthouse CLI (required for cleanup)
npm install -g @lighthouse-web3/sdk

# Configure environment
export BLOCKSCOUT_MCP_BASE="https://eth-sepolia.blockscout.com/api/v2"
export CHAIN_ID=11155111
export LIGHTHOUSE_API_KEY="your_key"
export LIGHTHOUSE_WALLET_PRIVATE_KEY="0x..."
export DATACOIN_CONTRACT_ADDRESS="0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC"

# Run worker
python run.py
```

**Expected output:**
```
✓ Blockscout MCP client initialized
✓ Lighthouse encryption configured
✓ HTTP server started on http://0.0.0.0:8787
✓ Fetched 47 swaps from Uniswap V3 USDC/WETH
✓ Lighthouse upload successful: QmXXX...
✓ Auto-cleanup: deleted 3 old files
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
export NEXT_PUBLIC_DATACOIN_ADDRESS="0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC"
export NEXT_PUBLIC_FAUCET_ADDRESS="0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB"
export NEXT_PUBLIC_CHAIN_ID=11155111
export NEXT_PUBLIC_METADATA_API="http://localhost:8787"

# Start dev server
npm run dev
```

**Visit:** http://localhost:3000

---

## Deployment

### Backend (Railway)

1. **Connect repo** to Railway
2. **Set env vars**:
   ```
   LIGHTHOUSE_API_KEY=...
   LIGHTHOUSE_WALLET_PRIVATE_KEY=0x...
   BLOCKSCOUT_MCP_BASE=https://eth-sepolia.blockscout.com/api/v2
   CHAIN_ID=11155111
   DATACOIN_CONTRACT_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
   ```
3. **Deploy** → Railway auto-detects nixpacks.toml
4. **Verify** → Check logs for "✅ Lighthouse upload successful"

### Frontend (Vercel)

1. **Connect repo** to Vercel
2. **Set env vars**:
   ```
   NEXT_PUBLIC_DATACOIN_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
   NEXT_PUBLIC_FAUCET_ADDRESS=0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB
   NEXT_PUBLIC_CHAIN_ID=11155111
   ```
3. **Deploy** → Auto-deploys from main branch
4. **Visit** → https://dexarb-data-unlock.vercel.app

---

## Key Features Explained

### 🔐 Lighthouse Native Encryption
- Uses Lighthouse's Kavach encryption (threshold BLS cryptography)
- Distributes key shards across 5 nodes
- Checks ERC20 balance on every decrypt attempt
- No backend decryption logic needed

**Code:** `apps/worker/lighthouse_native_encryption.py`

### 🔥 Token Burning Mechanism
- Frontend burns 1 DADC to `0xdead` before each decrypt
- Lighthouse checks updated balance
- When balance = 0, access denied
- Deflationary (tokens destroyed forever)

**Code:** `frontend/app/page.tsx` → `burnTokenForAccess()`

### 🧹 Auto-Cleanup
- Deletes old encrypted files after each upload
- Keeps only latest file (saves storage costs)
- Uses Lighthouse CLI for reliable deletion

**Code:** `apps/worker/lighthouse_cleanup.py`

### 📊 Arbitrage Detection
- Tracks 24h rolling window of token prices
- Calculates min/max/mean for each token
- Highlights profitable spreads
- Persists state across restarts

**Code:** `apps/worker/transform.py`

---

## Testing Access Control

```bash
# Test without tokens (should fail)
python scripts/verify_lighthouse_protection.py \
  --cid QmXXX... \
  --wallet 0xWithoutTokens

# Output: ❌ Access denied (balance = 0)

# Claim tokens from faucet
cast send 0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB \
  "claimTokens()" \
  --rpc-url https://ethereum-sepolia-rpc.publicnode.com \
  --private-key 0x...

# Test with tokens (should succeed)
python scripts/verify_lighthouse_protection.py \
  --cid QmXXX... \
  --wallet 0xWithTokens

# Output: ✅ Access granted (balance = 100 DADC)
```

---

## Documentation

- **[BURN_IMPLEMENTATION_COMPLETE.md](./BURN_IMPLEMENTATION_COMPLETE.md)** - Token burning implementation details
- **[LIGHTHOUSE_NATIVE_ENCRYPTION_REFACTOR_PLAN.md](./LIGHTHOUSE_NATIVE_ENCRYPTION_REFACTOR_PLAN.md)** - Encryption architecture
- **[DATACOIN_DEPLOYMENT.md](./DATACOIN_DEPLOYMENT.md)** - Smart contract deployment guide
- **[RAILWAY_ENV_VARS_REQUIRED.md](./RAILWAY_ENV_VARS_REQUIRED.md)** - Environment variable reference

---

## Why This Matters

**The Problem:** On-chain data is either:
1. **Free** → Anyone can scrape it (no monetization)
2. **Centralized** → Behind API keys/paywalls (censorship risk)

**This Solution:**
- Data lives on IPFS (decentralized, permanent)
- Encrypted with threshold cryptography (no single point of failure)
- Access gated by ERC20 tokens (programmable economics)
- Tokens burned on use (creates scarcity)

**Result:** True data markets on-chain. No middleman, no censorship, pay-per-use.

---

## Built With

- [Lighthouse](https://lighthouse.storage) - Decentralized encrypted storage (ETHOnline Sponsor)
- [1MB.io](https://1mb.io) - DataCoin creation platform
- [Blockscout](https://blockscout.com) - Blockchain data API
- [Railway](https://railway.app) - Backend deployment
- [Vercel](https://vercel.com) - Frontend deployment
- [ethers.js](https://ethers.org) - Ethereum interactions

---

## License

MIT - See [LICENSE](./LICENSE) for details

---

<div align="center">

**Made for ETHOnline 2025**

[🎯 Try Demo](https://dexarb-data-unlock.vercel.app) • [📜 Contracts](https://sepolia.etherscan.io/address/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC) • [🔥 Get Tokens](https://sepolia.etherscan.io/address/0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB#writeContract)

</div>

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
