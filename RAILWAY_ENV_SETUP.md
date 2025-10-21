# 🚀 Railway Environment Variables Setup

## ✅ BUILD SUCCESSFUL! Now Configure Environment Variables

Your Railway deployment is **building successfully**! The error you're seeing is expected - the app needs environment variables to run.

## 📋 Required Environment Variables

Go to your Railway dashboard → Your project → Variables tab and add these:

### **Core Required Variables**

```bash
BLOCKSCOUT_MCP_BASE=https://eth.blockscout.com/api/v2
CHAIN_ID=1
```

### **DEX Pool Configuration (Mainnet - High Activity)**

```bash
DEX_TYPE=v3
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
```

### **Worker Behavior (Demo-Optimized)**

```bash
WORKER_POLL_SECONDS=15
WORKER_HTTP_HOST=0.0.0.0
WORKER_HTTP_PORT=8787
WINDOW_MINUTES=2
PREVIEW_ROWS=8
LOG_LEVEL=INFO
MCP_INIT_ON_START=true
```

### **Additional Settings**

```bash
NETWORK_LABEL=Ethereum Mainnet
REFERENCE_ETH_PRICE_USD=2500.0
ENABLE_EMOJI_MARKERS=true
ENABLE_SPREAD_ALERTS=true
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300
```

---

## 🎯 Quick Copy-Paste Format for Railway

Railway accepts bulk variable entry. Copy everything below:

```
BLOCKSCOUT_MCP_BASE=https://eth.blockscout.com/api/v2
CHAIN_ID=1
DEX_TYPE=v3
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
WORKER_POLL_SECONDS=15
WORKER_HTTP_HOST=0.0.0.0
WORKER_HTTP_PORT=8787
WINDOW_MINUTES=2
PREVIEW_ROWS=8
LOG_LEVEL=INFO
MCP_INIT_ON_START=true
NETWORK_LABEL=Ethereum Mainnet
REFERENCE_ETH_PRICE_USD=2500.0
ENABLE_EMOJI_MARKERS=true
ENABLE_SPREAD_ALERTS=true
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300
```

---

## 📍 How to Add Variables in Railway

### Method 1: Bulk Add (Faster)
1. Go to Railway dashboard
2. Click your project → **Variables** tab
3. Click **"RAW Editor"** button (top right)
4. Paste all the variables above
5. Click **Save**

### Method 2: One-by-One
1. Go to Railway dashboard
2. Click your project → **Variables** tab
3. Click **"New Variable"**
4. Add each variable name and value
5. Click **Save** after each one

---

## 🔄 After Adding Variables

1. Railway will **automatically redeploy** with the new environment variables
2. Check the **Deployments** tab to monitor progress
3. Look for logs showing:
   ```
   🚀 DEX ARBITRAGE WORKER v1.1 - HACKATHON OPTIMIZED
   Network: Ethereum Mainnet (Chain ID: 1)
   DEX_POOL_A: 0x88e6...640
   Starting HTTP server on 0.0.0.0:8787
   ```

---

## 🌐 Generate Your Public URL

Once deployment succeeds:

1. Go to **Settings** tab
2. Scroll to **Networking** section
3. Click **"Generate Domain"**
4. Railway will give you a URL like: `https://your-app-name.up.railway.app`

---

## 🧪 Test Your Endpoints

Once deployed with a public URL:

```bash
# Health check
curl https://YOUR-RAILWAY-URL.up.railway.app/health

# Preview recent swaps (8 rows)
curl https://YOUR-RAILWAY-URL.up.railway.app/preview

# Metadata (row count, freshness)
curl https://YOUR-RAILWAY-URL.up.railway.app/metadata
```

---

## 📊 What These Pools Do

- **DEX_POOL_A**: `0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`
  - Uniswap V3 USDC/WETH 0.05% fee tier
  - ~$300M+ TVL (Total Value Locked)
  - **Extremely high activity** - swaps every few seconds

- **DEX_POOL_B**: `0x11b815efB8f581194ae79006d24E0d814B7697F6`
  - Uniswap V3 WETH/USDT 0.05% fee tier
  - Second-highest liquidity pool
  - **Very active** - constant swap activity

These are **live Ethereum Mainnet pools** - your worker will stream REAL swap data from production DEXes!

---

## 🎓 Understanding the Error

The error you saw:
```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
BLOCKSCOUT_MCP_BASE
  Field required [type=missing, input_value={}, input_type=dict]
CHAIN_ID
  Field required [type=missing, input_value={}, input_type=dict]
```

This is **EXPECTED** and means:
- ✅ Build succeeded (Python, pip, dependencies all installed)
- ✅ App started successfully
- ❌ App exited because required config is missing

Once you add the environment variables, the app will run perfectly!

---

## 🎉 Next Steps

1. **Add environment variables** (use bulk paste method above)
2. **Wait for automatic redeploy** (~2-3 minutes)
3. **Generate public domain** in Settings → Networking
4. **Test endpoints** with curl or browser
5. **Celebrate!** You've deployed a live DEX arbitrage scanner! 🚀

