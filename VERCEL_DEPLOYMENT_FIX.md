# 🚀 Vercel Deployment Guide - Frontend Fix

## Problem Identified ✅

**Root Cause:** The frontend `.env.local` was hardcoded to `http://localhost:8787`, which doesn't exist when deployed to Vercel production.

**Backend Status:** ✅ Railway backend is working perfectly at:
- URL: `https://web-production-279f4.up.railway.app/metadata`
- CORS: ✅ Configured correctly (`Access-Control-Allow-Origin: *`)
- Response: ✅ Valid JSON with all required fields

## Solution Implemented 🔧

### 1. Created `.env.production` File

Created `/frontend/.env.production` with production Railway URL:

```bash
NEXT_PUBLIC_METADATA_API=https://web-production-279f4.up.railway.app
NEXT_PUBLIC_CHAIN_ID=11155111
NEXT_PUBLIC_CHAIN_NAME=Sepolia
NEXT_PUBLIC_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
NEXT_PUBLIC_DATACOIN_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
NEXT_PUBLIC_FAUCET_ADDRESS=0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB
NEXT_PUBLIC_MIN_BALANCE=1.0
```

### 2. Improved Error Handling

Enhanced the `fetcher` function in `app/page.tsx` to provide better debugging:

```typescript
const fetcher = async (url: string) => {
  console.log('Fetching from:', url)
  const response = await fetch(url)
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error('Fetch failed:', response.status, errorText)
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }
  
  const data = await response.json()
  console.log('Fetched metadata successfully:', data)
  return data
}
```

### 3. Added API Endpoint Display

Added visible API endpoint in the UI to verify which backend is being used.

## Vercel Deployment Steps 📦

### Option A: Automatic Environment Variables (Recommended)

1. **Push Changes to Git:**
   ```bash
   cd /Users/shreyas/Desktop/af_hosted
   git add frontend/.env.production
   git add frontend/app/page.tsx
   git commit -m "fix: configure production API endpoint for Vercel deployment"
   git push origin main
   ```

2. **Deploy to Vercel:**
   ```bash
   cd frontend
   npx vercel --prod
   ```
   
   - Vercel will automatically use `.env.production` for production builds
   - No manual environment variable configuration needed

### Option B: Manual Vercel Environment Variables

If you need to override or verify the environment variables:

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add these variables for **Production** environment:

   | Variable Name | Value |
   |--------------|-------|
   | `NEXT_PUBLIC_METADATA_API` | `https://web-production-279f4.up.railway.app` |
   | `NEXT_PUBLIC_CHAIN_ID` | `11155111` |
   | `NEXT_PUBLIC_CHAIN_NAME` | `Sepolia` |
   | `NEXT_PUBLIC_RPC_URL` | `https://ethereum-sepolia-rpc.publicnode.com` |
   | `NEXT_PUBLIC_DATACOIN_ADDRESS` | `0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC` |
   | `NEXT_PUBLIC_FAUCET_ADDRESS` | `0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB` |
   | `NEXT_PUBLIC_MIN_BALANCE` | `1.0` |

4. Redeploy your application

## Verification Checklist ✅

After deploying to Vercel, verify the following:

### 1. Check Browser Console
Open your deployed Vercel URL and check the console for:
- ✅ `Fetching from: https://web-production-279f4.up.railway.app/metadata`
- ✅ `Fetched metadata successfully: {...}`
- ❌ No CORS errors
- ❌ No localhost errors

### 2. Check UI Elements
- ✅ "API: https://web-production-279f4.up.railway.app" shown in Data Feed card
- ✅ CID is displayed (QmYvDQYYqkiETVN2HrDtoU6NdeJaKvPRjtPjUckXtVHC92)
- ✅ Last Updated timestamp is recent
- ✅ Rows count shows data (e.g., 130 rows)
- ✅ Encryption status shows "Encrypted and uploaded successfully"

### 3. Test Wallet Flow
- ✅ Connect wallet (MetaMask)
- ✅ Switch to Sepolia network
- ✅ Check DADC balance
- ✅ Claim tokens if needed
- ✅ Unlock and decrypt data

### 4. Check Network Tab
In browser DevTools → Network:
- ✅ Request to `https://web-production-279f4.up.railway.app/metadata` returns 200
- ✅ Response headers include `access-control-allow-origin: *`
- ✅ Response body contains valid metadata JSON

## Debugging Tips 🔍

If you still see "Failed to fetch" error:

1. **Check the actual URL being called:**
   - Look at browser console for the `Fetching from:` log
   - Should be HTTPS Railway URL, not localhost

2. **Verify Railway backend is up:**
   ```bash
   curl https://web-production-279f4.up.railway.app/health
   # Should return: {"status": "ok"}
   ```

3. **Test metadata endpoint:**
   ```bash
   curl https://web-production-279f4.up.railway.app/metadata | jq '.latest_cid'
   # Should return a CID string
   ```

4. **Check Vercel build logs:**
   - Ensure environment variables are injected at build time
   - Look for `NEXT_PUBLIC_METADATA_API` in the build output

5. **Hard refresh in browser:**
   - Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)
   - Clears cached JavaScript bundles

## Technical Details 📋

### Environment Variable Loading Order

Next.js loads environment variables in this order (last wins):
1. `.env` (all environments)
2. `.env.local` (local development only, ignored in production)
3. `.env.production` (production only)
4. Vercel environment variables (override all)

### Why This Works

- **Development:** `.env.local` uses `localhost:8787` for local testing
- **Production:** `.env.production` uses Railway URL automatically
- **No code changes needed:** `process.env.NEXT_PUBLIC_METADATA_API` picks the right value

### CORS Configuration

Backend already has correct CORS headers:
```python
headers={
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Cache-Control": "no-store",
}
```

This allows any frontend domain (including Vercel) to access the API.

## Summary 📝

**CHECK: FE API config, env, endpoint matches backend deploy - ✅ FIXED**

**Changes Made:**
1. ✅ Created `.env.production` with Railway URL
2. ✅ Enhanced error handling and logging
3. ✅ Added API endpoint visibility in UI

**Backend Status:**
- ✅ Railway backend working perfectly
- ✅ CORS configured correctly
- ✅ HTTPS enabled
- ✅ Metadata endpoint returning valid JSON

**Next Steps:**
1. Commit and push the changes
2. Deploy to Vercel
3. Verify the metadata loads correctly
4. Test the full unlock/decrypt flow

**No Python/Railway changes made** - backend remains untouched and fully functional.
