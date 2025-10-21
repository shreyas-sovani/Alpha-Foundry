# Quick Railway Deploy - Step by Step

## 1. Merge Your Branch

On GitHub:
```
1. Go to: https://github.com/shreyas-sovani/Alpha-Foundry
2. Click "Pull requests" → "New pull request"
3. Select: base: main ← compare: lighthouse
4. Click "Create pull request"
5. Click "Merge pull request"
```

Or locally:
```bash
git checkout main
git merge lighthouse
git push origin main
```

## 2. Add Environment Variable to Railway

Go to Railway:
```
1. Visit: https://railway.app
2. Click your "Alpha-Foundry" project
3. Click "Variables" tab (left sidebar)
4. Click "+ New Variable"
5. Add:
   Name:  LIGHTHOUSE_API_KEY
   Value: 7e711ba4.5db09f1a785145159ab740254e63f070
6. Click "Add"
```

Railway will auto-redeploy with the new variable.

## 3. Wait for Deployment (2-3 minutes)

Watch the deployment:
```
- Click "Deployments" tab
- Wait for green checkmark ✓
- Or red X if failed
```

## 4. Test the Deployment

```bash
# Replace with your Railway URL
curl https://YOUR-APP.up.railway.app/health
```

Should return JSON with status "ok".

## 5. Test Lighthouse Upload (Optional)

If Railway CLI is installed:
```bash
railway link  # Link to your project
railway run bash  # SSH into container

# Inside container:
python -c "
from apps.worker.lighthouse_sdk_integration import LighthouseSDK
import os
lh = LighthouseSDK(api_key=os.getenv('LIGHTHOUSE_API_KEY'))
print('✓ Lighthouse SDK ready')
"
```

## Done! 🎉

Your Lighthouse integration is live. Upload will work from Railway's servers.

## Need Help?

- Check Railway logs: Click "View Logs" in dashboard
- Environment issues: `railway variables`
- Full guide: See `RAILWAY_LIGHTHOUSE_DEPLOY.md`
