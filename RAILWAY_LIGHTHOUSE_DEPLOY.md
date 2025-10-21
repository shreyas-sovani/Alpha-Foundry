# Railway Deployment Guide - Lighthouse Integration

## Pre-Deployment Checklist

### 1. Merge to Main Branch
```bash
# On GitHub: Create PR from lighthouse -> main and merge
# Or locally:
git checkout main
git merge lighthouse
git push origin main
```

### 2. Verify Railway Project Exists
- Go to https://railway.app
- Confirm your project is connected to GitHub repo

## Railway Environment Variables

Add these in Railway Dashboard → Your Project → Variables:

### Required Variables
```bash
LIGHTHOUSE_API_KEY=7e711ba4.5db09f1a785145159ab740254e63f070
```

### Existing Variables (Keep These)
```bash
# Your blockchain RPC endpoints
ALCHEMY_API_KEY=<your_alchemy_key>
BLOCKSCOUT_API_KEY=<your_blockscout_key>

# Any other environment variables you have
```

## Deployment Steps

### Option 1: Auto-Deploy (Recommended)
Railway will auto-deploy when you push to main:

```bash
git checkout main
git merge lighthouse
git push origin main
```

Wait 2-3 minutes for Railway to build and deploy.

### Option 2: Manual Deploy via Railway CLI
```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up
```

## Post-Deployment Testing

### 1. Check Health Endpoint
```bash
curl https://your-app.up.railway.app/health
```

Should return:
```json
{"status": "ok", ...}
```

### 2. Test Lighthouse Upload
SSH into Railway container or use your API:

```bash
# Via Railway CLI
railway run bash

# Then inside container:
python -c "
from apps.worker.lighthouse_sdk_integration import LighthouseSDK
import os

lh = LighthouseSDK(api_key=os.getenv('LIGHTHOUSE_API_KEY'))
print('SDK initialized successfully')
"
```

### 3. Test Full Encrypt + Upload
```bash
# Create a test file
echo 'test data' > /tmp/test.txt

# Upload it
python -c "
from apps.worker.lighthouse_sdk_integration import LighthouseSDK
from pathlib import Path
import os

lh = LighthouseSDK(api_key=os.getenv('LIGHTHOUSE_API_KEY'))
result = lh.encrypt_and_upload(Path('/tmp/test.txt'))
print(f'CID: {result[\"upload\"][\"cid\"]}')
print(f'Gateway: {result[\"upload\"][\"gateway_url\"]}')
"
```

## Verify Upload Success

If upload succeeds, you'll get:
```
CID: QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Gateway: https://gateway.lighthouse.storage/ipfs/QmXXX...
```

Visit the gateway URL to verify the encrypted file is accessible.

## Troubleshooting

### Build Fails
Check `requirements.txt` is committed:
```bash
git log --oneline | head -5
# Should see commit with "Lighthouse SDK integration"
```

### Runtime Error: Module Not Found
Railway may need to rebuild:
```bash
# Force rebuild
railway up --detach
```

### Lighthouse Upload Still Fails
1. Check Railway logs: `railway logs`
2. Verify LIGHTHOUSE_API_KEY is set: `railway variables`
3. Check if node.lighthouse.storage is accessible from Railway

### Environment Variable Not Found
Add via Railway Dashboard:
- Go to your project
- Variables tab
- Add: `LIGHTHOUSE_API_KEY`
- Redeploy

## Quick Reference

### Railway URLs
- Dashboard: https://railway.app
- Your project: https://railway.app/project/<project-id>
- Logs: Click "View Logs" in dashboard

### Useful Commands
```bash
# View logs
railway logs

# Check environment
railway variables

# SSH into container
railway run bash

# Restart service
railway restart
```

## Success Indicators

✅ Deployment successful when:
1. Build completes without errors
2. Health endpoint responds
3. Lighthouse SDK imports successfully
4. Upload test returns CID
5. Gateway URL shows encrypted file

## Next Steps After Successful Deployment

1. **Integrate with your worker**: Add upload to your DEX data pipeline
2. **Set up automation**: Schedule regular uploads
3. **Monitor CIDs**: Store CIDs for retrieval
4. **Test decryption**: Verify you can decrypt uploaded files

## Support

- Railway Docs: https://docs.railway.app
- Lighthouse Docs: https://docs.lighthouse.storage
- Your integration: See `LIGHTHOUSE_INTEGRATION.md`
