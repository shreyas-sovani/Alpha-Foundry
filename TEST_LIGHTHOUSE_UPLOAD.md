# Testing Lighthouse Upload on Railway

## Current Status ✅

Your Railway deployment is working, but **no files have been uploaded yet** because:
- The integration code is deployed but not triggered
- You need to manually test the upload
- Once tested, you can integrate it into your worker pipeline

## Quick Test (Option 1): Railway CLI

### 1. Install Railway CLI (if not installed)
```bash
npm i -g @railway/cli
```

### 2. Link to your project
```bash
cd /Users/shreyas/Desktop/af_hosted
railway link
# Select your project from the list
```

### 3. Run the test script
```bash
railway run python scripts/test_railway_upload.py
```

**Expected output:**
```
✓ SDK initialized
✓ Encryption successful!
✓ Upload successful!
🎯 RESULTS:
   CID: QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   Gateway: https://gateway.lighthouse.storage/ipfs/QmXXX...
```

### 4. Check Dashboard
Go to: https://files.lighthouse.storage/dashboard

You should now see your uploaded file! 🎉

## Quick Test (Option 2): Add API Endpoint

Add this to your worker to create an upload endpoint:

### 1. Create upload endpoint in `apps/worker/run.py`

Add this route:
```python
@app.post("/lighthouse/test-upload")
async def test_lighthouse_upload():
    """Test endpoint to upload to Lighthouse."""
    from lighthouse_sdk_integration import LighthouseSDK
    from pathlib import Path
    import os
    
    try:
        lh = LighthouseSDK(api_key=os.getenv("LIGHTHOUSE_API_KEY"))
        
        # Upload the latest DEX data
        file_path = Path(__file__).parent / "out/dexarb_latest.jsonl"
        
        if not file_path.exists():
            return {"error": "No data file found"}
        
        # Encrypt and upload
        result = lh.encrypt_and_upload(file_path, tag="dex_arb_test")
        
        return {
            "success": True,
            "cid": result["upload"]["cid"],
            "gateway_url": result["upload"]["gateway_url"],
            "file_size": result["encryption"]["encrypted_size"],
            "total_time": result["total_time"]
        }
        
    except Exception as e:
        return {"error": str(e)}
```

### 2. Deploy the change
```bash
git add apps/worker/run.py
git commit -m "Add test upload endpoint"
git push origin main
```

### 3. Test the endpoint
```bash
curl -X POST https://your-app.up.railway.app/lighthouse/test-upload
```

**Expected response:**
```json
{
  "success": true,
  "cid": "QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "gateway_url": "https://gateway.lighthouse.storage/ipfs/QmXXX...",
  "file_size": 361545,
  "total_time": 2.34
}
```

## Quick Test (Option 3): Railway Shell

### 1. SSH into Railway
```bash
railway run bash
```

### 2. Run test command
```bash
python scripts/test_railway_upload.py
```

## What You Should See on Dashboard

Once upload succeeds, on https://files.lighthouse.storage/dashboard you'll see:

| File Name | CID | Size | Date |
|-----------|-----|------|------|
| dexarb_latest.jsonl.enc | QmXXX... | 353 KB | Oct 21, 2025 |

## Troubleshooting

### "LIGHTHOUSE_API_KEY not found"
Check Railway environment variables:
```bash
railway variables
```

Should show:
```
LIGHTHOUSE_API_KEY=7e711ba4.5db09f1a785145159ab740254e63f070
```

### "Module not found: lighthouse_sdk_integration"
The test script needs to be run from Railway environment where the module is installed.

### "Connection timeout"
This means the upload is trying but failing. Check:
1. Railway logs: `railway logs`
2. Network connectivity from Railway to Lighthouse

### Upload succeeds but file not in dashboard
- Wait 30-60 seconds and refresh
- Check the CID directly: `https://gateway.lighthouse.storage/ipfs/YOUR_CID`
- Verify you're logged into the correct Lighthouse account

## After Successful Test

Once you see the file in your dashboard, you can:

1. **Integrate into worker**: Add automatic uploads to your DEX data pipeline
2. **Schedule uploads**: Set up cron jobs or event triggers
3. **Track CIDs**: Store CIDs in metadata for retrieval
4. **Set up monitoring**: Alert on upload failures

## Need the Actual Railway URL?

Check your Railway dashboard or run:
```bash
railway status
```

It will show your deployment URL like:
```
https://af-hosted-production-XXXX.up.railway.app
```

## Summary

✅ Your deployment is working  
⏸️ No files uploaded yet (expected)  
🎯 Run test script to upload first file  
🎉 Then check dashboard - file should appear!

Choose **Option 1** (Railway CLI) for quickest test.
