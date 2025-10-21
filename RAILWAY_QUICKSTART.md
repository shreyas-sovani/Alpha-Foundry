# 🚂 Railway Quick Start Checklist

## ⏱️ 10-Minute Deployment

### ✅ STEP 1: Railway Account (2 min)
- [ ] Go to https://railway.app
- [ ] Click "Login with GitHub"
- [ ] Authorize Railway

### ✅ STEP 2: GitHub Setup (3 min)
```bash
cd /Users/shreyas/Desktop/af_hosted
git init
git add .
git commit -m "Railway deployment ready"

# Create repo at: https://github.com/new
# Name: dex-arbitrage-worker

git remote add origin https://github.com/YOUR_USERNAME/dex-arbitrage-worker.git
git branch -M main
git push -u origin main
```

### ✅ STEP 3: Create Railway Project (1 min)
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose your repo
- [ ] Wait for initial build

### ✅ STEP 4: Environment Variables (2 min)
- [ ] Click service → "Variables" tab
- [ ] Click "Raw Editor"
- [ ] Paste all from `.env` file
- [ ] Save

**Critical Variables:**
```bash
BLOCKSCOUT_MCP_BASE=https://eth.blockscout.com/api/v2
CHAIN_ID=1
DEX_POOL_A=0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
DEX_POOL_B=0x11b815efB8f581194ae79006d24E0d814B7697F6
WORKER_HTTP_HOST=0.0.0.0
WORKER_HTTP_PORT=8787
```

### ✅ STEP 5: Networking (1 min)
- [ ] Click "Settings" tab
- [ ] Scroll to "Networking"
- [ ] Click "Generate Domain"
- [ ] **COPY YOUR URL**: `___________________.up.railway.app`

### ✅ STEP 6: Deploy (1 min)
- [ ] Click "Deployments" tab
- [ ] Watch logs for: `✓ HTTP server started`
- [ ] Status should be "Active"

### ✅ STEP 7: Test (1 min)
```bash
# Replace with YOUR Railway URL:
curl https://YOUR-URL.up.railway.app/health
curl https://YOUR-URL.up.railway.app/preview
curl https://YOUR-URL.up.railway.app/metadata
```

---

## 🎯 Your Live Endpoints

Once deployed, your endpoints will be:

```
Health:   https://YOUR-URL.up.railway.app/health
Preview:  https://YOUR-URL.up.railway.app/preview
Metadata: https://YOUR-URL.up.railway.app/metadata
```

**Use these in:**
- Hosted Agent configuration
- dApp UI
- Hackathon demos
- Future DataCoin integration

---

## 🔍 Debugging

**Check logs:**
1. Railway Dashboard → Your Service → "Logs"

**Common fixes:**
- Build fails → Check `requirements.txt` exists in `apps/worker/`
- Port error → Ensure `WORKER_HTTP_HOST=0.0.0.0`
- Crashes → Check all env vars are set
- No data → Verify Blockscout API is accessible

---

## 🔄 Updates

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push

# Railway auto-deploys! ✨
```

---

## 💡 Tips

1. **Monitor logs** during first deployment
2. **Wait 2-3 minutes** for first data to appear
3. **Test all 3 endpoints** before sharing
4. **Set up alerts** in Railway Settings → Notifications
5. **Upgrade to Starter ($5/mo)** for reliability during hackathon

---

## ✅ Success Criteria

- [ ] Railway URL is live
- [ ] `/health` returns `{"status": "ok"}`
- [ ] `/preview` returns swap data
- [ ] `/metadata` shows row count
- [ ] Logs show "CYCLE SUMMARY" every 15s
- [ ] No errors in Railway logs
- [ ] Endpoints accessible from anywhere

**You're LIVE! 🎉 Now go integrate with your agent!**
