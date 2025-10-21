# 🎯 COMPLETE RAILWAY DEPLOYMENT - START HERE

## 📖 Table of Contents
1. [What You're Deploying](#what-youre-deploying)
2. [10-Minute Deployment Steps](#10-minute-deployment-steps)
3. [Testing Your Endpoints](#testing-your-endpoints)
4. [Monitoring & Debugging](#monitoring--debugging)
5. [Updating After Deployment](#updating-after-deployment)
6. [Cost & Scaling](#cost--scaling)
7. [Troubleshooting](#troubleshooting)

---

## 🎬 What You're Deploying

**Your DEX Arbitrage Worker** is a Python service that:
- ✅ Runs 24/7 (polls every 15 seconds)
- ✅ Fetches live swap data from Uniswap V3 pools
- ✅ Processes and enriches the data
- ✅ Serves 3 HTTP endpoints:
  - `/health` - Service health check
  - `/preview` - Latest 8 swaps with analytics
  - `/metadata` - Dataset metadata and freshness

**Why Railway?**
- Supports long-running processes (unlike Vercel)
- Persistent storage for state files
- Auto-deploys from GitHub
- Simple pricing ($5/month after free trial)

---

## 🚀 10-Minute Deployment Steps

### **STEP 1: GitHub Setup** (3 minutes)

Your code needs to be on GitHub first. Run these commands:

```bash
# Navigate to your project
cd /Users/shreyas/Desktop/af_hosted

# Stage all files
git add .

# Commit (if there are changes)
git commit -m "Add Railway deployment configs"

# Check git status
git status
```

**If you see "nothing to commit"**, you're ready!

**If you DON'T have a GitHub remote yet:**

1. **Create a new repo on GitHub:**
   - Go to: https://github.com/new
   - Repository name: `dex-arbitrage-worker`
   - Description: "DEX arbitrage data worker with live swap monitoring"
   - Public or Private: **Your choice** (both work with Railway)
   - **DON'T** check "Initialize this repository with:"
   - Click "Create repository"

2. **Link your local repo:**
   ```bash
   # Replace YOUR_USERNAME with your GitHub username
   git remote add origin https://github.com/YOUR_USERNAME/dex-arbitrage-worker.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

3. **Verify:** Go to your GitHub repo URL - you should see all your files!

✅ **Checkpoint 1:** Your code is on GitHub

---

### **STEP 2: Create Railway Account** (2 minutes)

1. **Open**: https://railway.app

2. **Click**: "Start a New Project" or "Login"

3. **Choose**: "Login with GitHub"

4. **Authorize Railway:**
   - Click "Authorize railway-app"
   - This lets Railway access your repos

5. **Complete profile** (if first time):
   - Enter name/email
   - Skip payment for now (free trial available)

✅ **Checkpoint 2:** You're logged into Railway dashboard

---

### **STEP 3: Create New Project** (1 minute)

1. **In Railway dashboard**, click: **"+ New Project"**

2. **Select**: "Deploy from GitHub repo"

3. **Configure GitHub App** (if first time):
   - Click "Configure GitHub App"
   - Select: "All repositories" or choose specific repo
   - Click "Install & Authorize"

4. **Choose your repo:**
   - Find: "dex-arbitrage-worker" (or your repo name)
   - Click on it

5. **Railway starts building:**
   - You'll see "Building..." status
   - This first build may fail - that's OK! We need to set environment variables

✅ **Checkpoint 3:** Project created, initial build running

---

### **STEP 4: Configure Environment Variables** (3 minutes)

This is the **most critical step** - your worker needs these to run.

1. **Click on your service** (the box with your repo name)

2. **Click the "Variables" tab**

3. **Click "RAW Editor"** (top right) - this is easier for bulk paste

4. **Paste ALL of these** (copy from below):

```bash
BLOCKSCOUT_MCP_BASE=https://eth.blockscout.com/api/v2
AUTOSCOUT_BASE=https://dex-arbitrage-mainnet.cloud.blockscout.com
CHAIN_ID=1
NETWORK_LABEL=Ethereum Mainnet
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
DEX_TYPE=v3
WORKER_POLL_SECONDS=15
WINDOW_MINUTES=2
MAX_ROWS_PER_ROTATION=1000
PREVIEW_ROWS=8
MCP_INIT_ON_START=true
MIN_SWAPS_PER_CYCLE=1
STALE_THRESHOLD_SECONDS=300
ENABLE_EMOJI_MARKERS=true
ENABLE_SPREAD_ALERTS=true
LAST_BLOCK_STATE_PATH=state/last_block.json
DATA_OUT_DIR=apps/worker/out
LOG_LEVEL=INFO
REFERENCE_ETH_PRICE_USD=2500.0
WINDOW_STRATEGY=timestamp
BLOCK_LOOKBACK=100
MAX_PAGES_PER_CYCLE=5
ROLLING_WINDOW_SIZE=1000
ROLLING_WINDOW_UNIT=rows
DECIMALS_CACHE_PATH=state/erc20_decimals.json
BLOCK_TS_CACHE_PATH=state/block_ts.json
PREVIEW_PATH=apps/worker/out/preview.json
METADATA_PATH=apps/worker/out/metadata.json
SCHEMA_VERSION=1.1
WORKER_HTTP_PORT=8787
WORKER_HTTP_HOST=0.0.0.0
```

5. **Click "Update Variables"** (bottom right)

6. **Wait for auto-redeploy** - Railway will rebuild with your env vars

✅ **Checkpoint 4:** Environment variables set, redeploying

---

### **STEP 5: Generate Public URL** (1 minute)

1. **Still in your service**, click the **"Settings" tab**

2. **Scroll down to "Networking"** section

3. **Click "Generate Domain"**
   - Railway creates a public URL like: `dex-worker-production-ab12cd.up.railway.app`

4. **IMPORTANT: Copy this URL!** Write it down:
   ```
   My Railway URL: _________________________________
   ```

5. **Optional**: Change service name
   - At top of Settings, click the name
   - Rename to: `dex-worker`
   - This makes logs easier to find

✅ **Checkpoint 5:** Public URL generated

---

### **STEP 6: Watch Deployment** (2 minutes)

1. **Click the "Deployments" tab**

2. **Click on the latest deployment** (should say "BUILDING" or "DEPLOYING")

3. **Watch the logs** - you should see:
   ```
   Installing dependencies...
   ✓ Python 3.10 installed
   ✓ Installing requirements from apps/worker/requirements.txt
   ✓ Build completed
   Starting service...
   ```

4. **Wait for these success messages:**
   ```
   ✓ HTTP server started on http://0.0.0.0:8787
   🚀 DEX ARBITRAGE WORKER v1.1 - HACKATHON OPTIMIZED
   ✓ MCP client created
   ```

5. **Deployment status changes to: "Active" 🟢**

✅ **Checkpoint 6:** Service is live!

---

### **STEP 7: Test Your Endpoints** (1 minute)

Now let's verify everything works!

**Replace `YOUR-URL` with your Railway URL in these commands:**

```bash
# Test 1: Health check (should return immediately)
curl https://YOUR-URL.up.railway.app/health

# Expected: {"status": "ok"}

# Test 2: Preview endpoint (may take 30-60s to populate first time)
curl https://YOUR-URL.up.railway.app/preview | head -20

# Expected: JSON with "header" and "preview_rows"

# Test 3: Metadata
curl https://YOUR-URL.up.railway.app/metadata

# Expected: {"schema_version": "1.1", "rows": ..., "last_updated": ...}
```

**Or test in browser:**
- Health: https://YOUR-URL.up.railway.app/health
- Preview: https://YOUR-URL.up.railway.app/preview
- Metadata: https://YOUR-URL.up.railway.app/metadata

✅ **Checkpoint 7:** All endpoints responding! 🎉

---

## 🧪 Testing Your Endpoints

### **Health Endpoint**
```bash
curl https://YOUR-URL.up.railway.app/health
```

**Expected Response:**
```json
{"status": "ok"}
```

**What it means:**
- ✅ Service is running
- ✅ HTTP server is responding
- ✅ No immediate errors

---

### **Preview Endpoint**
```bash
curl https://YOUR-URL.up.railway.app/preview | jq '.'
```

**Expected Response:**
```json
{
  "header": {
    "updated_ago_seconds": 15,
    "window_minutes": 2,
    "activity_swaps_per_min": 2.5,
    "pool_ids": ["0x88e6A0c2...", "0x11b815ef..."],
    "spread_percent": 0.15,
    "status_emoji": "🚀",
    "activity_ring": "12 swaps/2min | Updated 15s ago"
  },
  "preview_rows": [
    {
      "timestamp": 1729536245,
      "tx_hash": "0xabc123...",
      "token_in_symbol": "USDC",
      "token_out_symbol": "WETH",
      "amount_in_normalized": "1000.50",
      "amount_out_normalized": "0.4",
      "normalized_price": 2501.25,
      "delta_vs_ma": 0.5,
      "swap_value_usd": 1000.50,
      "emoji_marker": "🔥",
      "is_new": true,
      "explorer_link": "https://etherscan.io/tx/0xabc123..."
    }
    // ... 7 more swaps
  ],
  "total_rows": 150,
  "last_updated": "2025-10-21T12:34:56Z"
}
```

**What to check:**
- ✅ `updated_ago_seconds` < 60 (data is fresh)
- ✅ `activity_swaps_per_min` > 0 (pools are active)
- ✅ `preview_rows` has 8 items
- ✅ `total_rows` > 0

**If preview_rows is empty:**
- Wait 30-60 seconds for first data
- Check logs for errors
- Verify pools have recent activity on Etherscan

---

### **Metadata Endpoint**
```bash
curl https://YOUR-URL.up.railway.app/metadata | jq '.'
```

**Expected Response:**
```json
{
  "schema_version": "1.1",
  "last_updated": "2025-10-21T12:34:56Z",
  "rows": 150,
  "freshness_minutes": 0,
  "latest_cid": null,
  "format": "jsonl",
  "fields": ["timestamp", "block_number", "tx_hash", ...]
}
```

**What to check:**
- ✅ `rows` increases over time
- ✅ `freshness_minutes` stays low (< 5)
- ✅ `last_updated` is recent

---

## 📊 Monitoring & Debugging

### **View Live Logs**

1. **Go to Railway dashboard**
2. **Click your service**
3. **Click "Logs" tab**

**What to look for:**

✅ **Good signs:**
```
🔄 CYCLE SUMMARY - HACKATHON DEMO OPTIMIZED
  Logs fetched: 50 across 1 pages
  Produced rows: 5
  Rows: 145 -> 150 (delta: +5)
✅ VALIDATION: PASS - Dynamic and Useful Data
```

⚠️ **Warning signs:**
```
⚠️ Insufficient activity: only 0 new swaps
⚠️ Stale data: latest swap is 320s old
```

❌ **Error signs:**
```
Failed to get latest block: Connection refused
ModuleNotFoundError: No module named 'aiohttp'
Error 429: Rate limit exceeded
```

---

### **Monitor Resource Usage**

1. **Click "Metrics" tab**
2. **Check:**
   - **CPU**: Should be < 50% normally
   - **Memory**: Should be < 300MB (free tier has 512MB)
   - **Network**: Shows API calls to Blockscout

**If memory is high:**
- Reduce `ROLLING_WINDOW_SIZE` to 500
- Reduce `PREVIEW_ROWS` to 5
- Or upgrade to Starter plan ($5/mo, 8GB RAM)

---

### **Check Deployment Status**

**Status indicators:**
- 🟢 **ACTIVE** - Service is running
- 🟡 **BUILDING** - Deploying new version
- 🔴 **CRASHED** - Service failed (check logs!)
- 🟠 **SLEEPING** - Free tier idle timeout (first request wakes it)

---

## 🔄 Updating After Deployment

**Every time you make changes locally:**

```bash
# 1. Make your changes to code
# (edit files in VS Code)

# 2. Stage and commit
git add .
git commit -m "Updated worker settings"

# 3. Push to GitHub
git push

# 4. Railway auto-deploys! ✨
# (watch in Deployments tab)
```

**To rollback:**
1. Go to "Deployments" tab
2. Find a successful old deployment
3. Click the "⋯" menu → "Redeploy"

---

## 💰 Cost & Scaling

### **Plans:**

| Plan | Cost | RAM | CPU | Storage | Execution Hours |
|------|------|-----|-----|---------|-----------------|
| **Trial** | Free | 512MB | Shared | 1GB | 500 hrs (~$5) |
| **Starter** | $5/mo | 8GB | Shared | 100GB | $5/mo credit + usage |
| **Pro** | $20/mo | 32GB | Dedicated | 100GB | More included |

### **Estimated Costs:**

**Your worker runs 24/7, so:**
- 730 hours/month (full month)
- At $0.01/hour = **~$7.30/month**

**Recommendation:**
- ✅ Start with **Trial** (free $5 credit = 500 hours)
- ✅ Upgrade to **Starter** ($5/mo) when trial ends
- ✅ Use **Starter** for hackathon/production

### **Monitor Usage:**
1. Click your avatar (top right)
2. Click "Usage"
3. See current spend vs. credit

---

## 🛡️ Security & Best Practices

### **✅ Already Done:**
- ✅ `.env` is gitignored
- ✅ Secrets are in Railway (not in code)
- ✅ CORS is enabled for public access
- ✅ Health checks configured

### **Additional Hardening:**

**1. Rate Limiting** (if you get abuse):
```python
# Add to http_server.py (future enhancement)
from aiohttp import web
from aiohttp_ratelimit import RateLimiter

# Limit to 60 requests/minute per IP
rate_limiter = RateLimiter(max_requests=60, time_window=60)
```

**2. API Authentication** (for paid endpoints):
```python
# Check for API key header
api_key = request.headers.get("X-API-Key")
if api_key != os.getenv("API_KEY"):
    return web.json_response({"error": "Unauthorized"}, status=401)
```

**3. Custom Domain** (professional look):
1. Settings → Networking → Custom Domain
2. Add: `api.yourproject.com`
3. Update DNS (Railway shows instructions)
4. SSL is automatic!

---

## 🐛 Troubleshooting

### **Issue 1: "Module not found" Error**

**Error in logs:**
```
ModuleNotFoundError: No module named 'aiohttp'
```

**Fix:**
1. Check `apps/worker/requirements.txt` has all dependencies
2. Verify `railway.json` has correct build command
3. Trigger new deployment (Settings → Redeploy)

---

### **Issue 2: "Port binding failed"**

**Error in logs:**
```
OSError: [Errno 48] Address already in use
```

**Fix:**
1. Verify `WORKER_HTTP_HOST=0.0.0.0` (not localhost)
2. Verify `WORKER_HTTP_PORT=8787`
3. Redeploy

---

### **Issue 3: "No data in preview"**

**Symptoms:**
- `/preview` returns empty `preview_rows: []`
- `/metadata` shows `rows: 0`

**Fix:**
1. **Wait 2-3 minutes** - first data takes time
2. **Check logs** - look for "CYCLE SUMMARY"
3. **Verify pools are active:**
   - Go to Etherscan
   - Search for pool address (e.g., `0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640`)
   - Check recent "Swap" events
4. **If pools are quiet**, switch to mainnet active pools (see `.env.mainnet.recommended`)

---

### **Issue 4: "Rate limit exceeded"**

**Error in logs:**
```
Error 429: Too Many Requests
```

**Fix:**
1. Increase `WORKER_POLL_SECONDS` from 15 to 30
2. Reduce `MAX_PAGES_PER_CYCLE` from 5 to 3
3. Blockscout public API has rate limits
4. Consider upgrading to paid Blockscout API

---

### **Issue 5: "Out of memory"**

**Error in logs:**
```
Killed (signal 9)
```

**Fix:**
1. Reduce `ROLLING_WINDOW_SIZE` to 500
2. Reduce `PREVIEW_ROWS` to 5
3. Set `LOG_LEVEL=WARNING` (less verbose)
4. Or upgrade to Starter plan (8GB RAM)

---

### **Issue 6: "Deployment stuck in 'Building'"**

**Symptoms:**
- Deployment shows "BUILDING" for > 5 minutes
- No logs appearing

**Fix:**
1. Cancel deployment (⋯ menu → Cancel)
2. Check GitHub Actions - might be build issue
3. Verify `railway.json` syntax is valid
4. Manually trigger: Settings → Redeploy

---

## 🎯 Production Checklist

Before sharing with hackathon judges/users:

- [ ] All 3 endpoints responding correctly
- [ ] Logs show no errors for 10+ minutes
- [ ] `preview` updates every 15-30 seconds
- [ ] `updated_ago_seconds` stays < 60
- [ ] `activity_swaps_per_min` > 0
- [ ] Railway monitoring/alerts configured
- [ ] Custom domain set (optional but professional)
- [ ] README updated with Railway URL
- [ ] Hosted Agent connected and tested
- [ ] Load tested (send 100+ requests)

---

## 📞 Getting Help

**Railway Resources:**
- **Docs**: https://docs.railway.app
- **Discord**: https://discord.gg/railway (VERY responsive!)
- **Status**: https://status.railway.app
- **Help**: help@railway.app

**Common Quick Fixes:**
1. **Redeploy** - Settings → Redeploy (fixes 80% of issues)
2. **Check logs** - Almost always shows the problem
3. **Verify env vars** - Variables tab → Check all are set
4. **Ask Discord** - Railway team is super helpful

---

## 🏁 Success!

**Your worker is now:**
- ✅ Running 24/7 on Railway
- ✅ Fetching live mainnet swap data
- ✅ Serving public endpoints globally
- ✅ Auto-deploying from GitHub
- ✅ Monitored and logged
- ✅ Ready for hackathon demo

**Next steps:**
1. ✅ Update your Hosted Agent with Railway URL
2. ✅ Test end-to-end (Agent → Railway → Blockscout)
3. ✅ Add Railway URL to project documentation
4. ✅ Share with team/judges
5. ✅ Monitor during demo for uptime

---

**🎉 CONGRATULATIONS! You're live on Railway!**

Your endpoints:
- Health: `https://YOUR-URL.up.railway.app/health`
- Preview: `https://YOUR-URL.up.railway.app/preview`
- Metadata: `https://YOUR-URL.up.railway.app/metadata`

**Share these with confidence!** 🚀
