# ⚡ RAILWAY DEPLOYMENT - FINAL STEP

## 🎯 Action Required: Add Lighthouse API Key

### 1. Get Your API Key
1. Go to: https://files.lighthouse.storage/dashboard
2. Click **"API Key"** in the left sidebar
3. Click **"Create New API Key"** or copy existing one
4. Copy the key (looks like: `7d8e9f0a-1b2c-3d4e-5f6g-7h8i9j0k1l2m`)

### 2. Add to Railway
1. Go to your Railway project: https://railway.app/project/[your-project-id]
2. Select your service (the worker)
3. Click **"Variables"** tab
4. Click **"+ New Variable"**
5. Add:
   ```
   Variable: LIGHTHOUSE_API_KEY
   Value: [paste your API key here]
   ```
6. Click **"Add"**

### 3. Enable Upload (if not already set)
Add another variable:
```
Variable: LIGHTHOUSE_ENABLE_UPLOAD
Value: true
```

### 4. Deploy
Railway will **automatically redeploy** when you add environment variables.

Wait 1-2 minutes for deployment to complete.

### 5. Verify Upload Works

#### Check Logs:
```bash
railway logs --follow
```

Look for these messages every cycle (~15 seconds):
```
📤 Uploading dexarb_latest.jsonl to Lighthouse...
✅ Lighthouse upload successful in 2.45s
   CID: QmXxxx...
   View: https://files.lighthouse.storage/viewFile/QmXxxx...
✓ Lighthouse CID: QmXxxx...
```

#### Check Dashboard:
https://files.lighthouse.storage/dashboard

You should see:
- New file appears every ~15 seconds (each worker cycle)
- File name: `dexarb_latest_[timestamp].jsonl.enc`
- Status: Encrypted ✅
- Tag: `dexarb_Ethereum Mainnet` (or your network)

#### Check Metadata Endpoint:
```bash
curl https://[your-app].up.railway.app/metadata | jq '.latest_cid'
```

Should output:
```json
"QmXxxx..."
```

### 6. Success Indicators

✅ **Railway logs show upload messages**  
✅ **No error messages in logs**  
✅ **Files appear in Lighthouse dashboard**  
✅ **metadata.json contains CID**  
✅ **File count increases every cycle**  

## 🎉 You're Done!

Your worker is now automatically:
1. ✅ Fetching DEX arbitrage data from Blockscout
2. ✅ Transforming and enriching swaps
3. ✅ Applying rolling window (24h data)
4. ✅ **Encrypting and uploading to Lighthouse IPFS**
5. ✅ Serving data via HTTP endpoints
6. ✅ Running on Railway (production)

## 🏆 Prize Eligibility

You're now eligible for the **ETHOnline Lighthouse Challenge**! 🎊

Your integration includes:
- ✅ Official Lighthouse Python SDK
- ✅ AES-256-GCM encryption
- ✅ Decentralized IPFS storage
- ✅ Automatic upload pipeline
- ✅ CID tracking in metadata
- ✅ Production deployment

## 🔗 Important Links

- **Lighthouse Dashboard**: https://files.lighthouse.storage/dashboard
- **Your Railway App**: Check Railway dashboard for URL
- **Preview Endpoint**: `https://[your-app].up.railway.app/preview`
- **Metadata Endpoint**: `https://[your-app].up.railway.app/metadata`
- **Health Check**: `https://[your-app].up.railway.app/health`

## 🐛 Troubleshooting

### Logs show "API key not set"
- Make sure `LIGHTHOUSE_API_KEY` is added to Railway variables
- Wait for automatic redeployment

### Logs show "SDK not available"
- Check `requirements.txt` includes: `lighthouseweb3>=0.1.5`
- Force redeploy if needed

### No files in dashboard
- Check if `LIGHTHOUSE_ENABLE_UPLOAD=true` is set
- Verify API key is correct
- Check Railway logs for upload errors

---

**Status**: 🚀 **READY TO DEPLOY**  
**Next**: Add `LIGHTHOUSE_API_KEY` to Railway → Automatic deployment → Verify!
