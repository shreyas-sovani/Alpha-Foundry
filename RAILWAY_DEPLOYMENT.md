# 🚂 Railway.app Deployment Guide - Step by Step

## 📚 What is Railway?

Railway is a **modern cloud platform** designed for developers who need to deploy:
- Long-running services (like your DEX worker)
- Background jobs
- APIs and web servers
- Databases

**Key Benefits for Your Project:**
- ✅ Supports 24/7 Python workers
- ✅ Persistent storage for your state files
- ✅ Auto-deploys from GitHub
- ✅ Simple environment variables
- ✅ Built-in monitoring and logs
- ✅ Custom domains and HTTPS
- ✅ $5/month starter plan (500 hours free trial)

---

## 🎯 Step-by-Step Deployment (10 Minutes)

### **STEP 1: Create Railway Account** (2 minutes)

1. **Go to**: https://railway.app
2. **Click**: "Start a New Project" or "Login"
3. **Sign up with GitHub**:
   - Click "Login with GitHub"
   - Authorize Railway to access your repos
   - This connects your GitHub account

✅ **Checkpoint**: You should now see the Railway dashboard

---

### **STEP 2: Push Your Code to GitHub** (3 minutes)

Your code needs to be in a GitHub repository for Railway to deploy it.

**If you already have a GitHub repo:**
- Skip to Step 3

**If you DON'T have a GitHub repo yet:**

```bash
# In your terminal, navigate to your project:
cd /Users/shreyas/Desktop/af_hosted

# Initialize git (if not already done):
git init

# Add all files:
git add .

# Commit:
git commit -m "Initial commit - DEX worker ready for Railway"

# Create a new repo on GitHub:
# 1. Go to https://github.com/new
# 2. Name it: "dex-arbitrage-worker"
# 3. Make it Public or Private (your choice)
# 4. DON'T initialize with README (you already have one)
# 5. Click "Create repository"

# Link your local repo to GitHub (replace YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/dex-arbitrage-worker.git

# Push to GitHub:
git branch -M main
git push -u origin main
```

✅ **Checkpoint**: Your code is now on GitHub

---

### **STEP 3: Create Railway Project** (2 minutes)

1. **In Railway Dashboard**, click: **"New Project"**

2. **Select**: "Deploy from GitHub repo"

3. **Choose your repository**: 
   - Find "dex-arbitrage-worker" (or whatever you named it)
   - Click on it

4. **Railway will auto-detect Python** and start building

5. **Wait for initial build** (this will fail - that's OK! We need to configure it first)

✅ **Checkpoint**: You should see a project with one service

---

### **STEP 4: Configure Environment Variables** (3 minutes)

Now we'll add all your `.env` variables to Railway:

1. **In your Railway project**, click on your service

2. **Click the "Variables" tab**

3. **Click "+ New Variable"** and add each of these:

```bash
# Copy these EXACT values from your .env file:

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

# IMPORTANT: Set this to Railway's internal port
WORKER_HTTP_PORT=8787
WORKER_HTTP_HOST=0.0.0.0
```

**Pro Tip**: Railway has a "Raw Editor" button - click it and paste all at once!

✅ **Checkpoint**: All variables are set

---

### **STEP 5: Configure Deployment Settings** (1 minute)

1. **Still in your service**, click the **"Settings" tab**

2. **Service Name**: Change to something memorable like `dex-worker`

3. **Scroll down to "Networking"**:
   - Click **"Generate Domain"**
   - Railway will give you a public URL like: `dex-worker-production.up.railway.app`
   - **COPY THIS URL** - you'll need it!

4. **Scroll to "Deploy"**:
   - **Start Command** should be: `cd apps/worker && python run.py`
   - If not, click "Custom Start Command" and paste that

5. **Healthcheck** (optional but recommended):
   - Path: `/health`
   - Timeout: 60 seconds

✅ **Checkpoint**: Service is configured

---

### **STEP 6: Deploy!** (1 minute)

1. **Click the "Deployments" tab**

2. **Click "Deploy"** (or it might auto-deploy)

3. **Watch the logs** as Railway:
   - Installs Python
   - Installs your dependencies
   - Starts your worker

4. **Look for this in logs**:
   ```
   ✓ HTTP server started on http://0.0.0.0:8787
   ```

✅ **Checkpoint**: Your worker is LIVE! 🎉

---

### **STEP 7: Test Your Endpoints** (2 minutes)

Your Railway URL is: `https://dex-worker-production.up.railway.app`

**Test in your browser or terminal:**

```bash
# Health check:
curl https://YOUR-RAILWAY-URL.up.railway.app/health

# Preview endpoint:
curl https://YOUR-RAILWAY-URL.up.railway.app/preview

# Metadata:
curl https://YOUR-RAILWAY-URL.up.railway.app/metadata
```

**Expected response (preview):**
```json
{
  "header": {
    "updated_ago_seconds": 15,
    "activity_swaps_per_min": 2.5,
    "status_emoji": "🚀"
  },
  "preview_rows": [...],
  "total_rows": 150
}
```

✅ **Checkpoint**: Endpoints are working!

---

## 🔍 Monitoring & Debugging

### **View Live Logs:**
1. Go to your Railway project
2. Click your service
3. Click "Logs" tab
4. Watch real-time output

### **Common Issues:**

**1. "Module not found" error:**
- **Fix**: Check that `railway.json` has the correct build command
- Redeploy after fixing

**2. "Port binding failed":**
- **Fix**: Make sure `WORKER_HTTP_HOST=0.0.0.0` in environment variables
- Railway uses internal port 8787 by default

**3. "Out of memory":**
- **Fix**: Your free tier has 512MB RAM
- Reduce `ROLLING_WINDOW_SIZE` to 500 or lower
- Or upgrade to Starter plan ($5/mo) for 8GB RAM

**4. Worker crashes after a few minutes:**
- **Fix**: Check logs for errors
- Make sure all environment variables are set correctly
- Verify Blockscout API is accessible

### **View Resource Usage:**
1. Click "Metrics" tab in Railway
2. See CPU, RAM, Network usage
3. Railway will auto-scale if needed (on paid plans)

---

## 🔄 Updating Your Code

**After you make changes locally:**

```bash
# Commit your changes:
git add .
git commit -m "Updated worker settings"

# Push to GitHub:
git push

# Railway auto-deploys! 🎉
```

**To rollback:**
1. Go to "Deployments" tab
2. Click on an old successful deployment
3. Click "Redeploy"

---

## 💰 Cost & Limits

### **Free Trial (Hobby Plan):**
- $5 credit (500 execution hours)
- 512MB RAM, 1 vCPU
- 1GB disk space
- Good for testing/demos

### **Starter Plan ($5/month):**
- $5 credit + $5/month subscription
- 8GB RAM, shared CPU
- 100GB disk
- **Perfect for your hackathon**

### **Pro Plan ($20/month):**
- Priority builds
- More resources
- Team collaboration

**Recommendation**: Start with free trial, upgrade to Starter when you need reliability.

---

## 🛡️ Security Best Practices

### **1. Keep Secrets in Railway (not .env):**
- Never commit `.env` to GitHub
- `.gitignore` already excludes it ✅

### **2. Use Railway's Secret Variables:**
- For API keys, mark as "Secret" in Railway
- They'll be hidden in logs and UI

### **3. Enable CORS (Already Done):**
- Your `http_server.py` already has:
  ```python
  "Access-Control-Allow-Origin": "*"
  ```

### **4. Rate Limiting:**
- Add API keys if you want to gate access
- Use Railway's network policies (Pro plan)

---

## 🚀 Going Production-Ready

### **1. Custom Domain:**
1. In Railway, click "Settings" > "Networking"
2. Click "Custom Domain"
3. Add your domain: `api.yourproject.com`
4. Follow DNS instructions (add CNAME record)

### **2. Persistent Storage:**
Your state files (`state/*.json`) persist on Railway's disk!

**To verify:**
```bash
# SSH into your Railway service (Pro plan only)
railway shell

# Check files:
ls -la state/
```

**For better persistence**, consider:
- **Railway Volumes** (paid plans)
- **External storage**: AWS S3, Cloudflare R2, etc.

### **3. Monitoring & Alerts:**
- Set up **Railway notifications** (Settings > Notifications)
- Get alerts for crashes, high CPU, etc.

### **4. Scaling (When You Need It):**
- Railway auto-scales on higher plans
- Or manually add more replicas (Settings > Scaling)

---

## 🎯 Next Steps for Your Hackathon

1. ✅ **Get Railway URL** - use it in your agent
2. ✅ **Update Agent Code** - point to Railway endpoints
3. ✅ **Test End-to-End** - agent → Railway → Blockscout
4. ✅ **Monitor Logs** - watch for errors during demo
5. ✅ **Add to Documentation** - include Railway URL in README

---

## 📞 Support & Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Railway Status**: https://status.railway.app
- **Pricing**: https://railway.app/pricing

---

## ✅ Success Checklist

- [ ] Railway account created
- [ ] GitHub repo connected
- [ ] Environment variables set
- [ ] Service deployed successfully
- [ ] Endpoints responding (health, preview, metadata)
- [ ] Logs show worker polling every 15s
- [ ] Agent connected to Railway endpoints
- [ ] Custom domain configured (optional)
- [ ] Monitoring/alerts set up

---

**You're now LIVE on Railway! 🎉**

Your endpoints are:
- Health: `https://YOUR-URL.up.railway.app/health`
- Preview: `https://YOUR-URL.up.railway.app/preview`
- Metadata: `https://YOUR-URL.up.railway.app/metadata`

**Share these with:**
- Your Hosted Agent
- Hackathon judges
- dApp UI
- Future DataCoin buyers

---

## 🆘 Need Help?

If you hit any issues:
1. Check Railway logs first
2. Look for error messages
3. Verify environment variables
4. Check Blockscout API status
5. Ask in Railway Discord (very responsive!)

**Good luck with your hackathon! 🚀**
