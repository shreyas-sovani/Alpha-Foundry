# Railway Deployment Debug Checklist

## Current Status (Commit 67a8cf6)

**Fix Applied:** `.dockerignore` prevents `node_modules` from being overwritten

## What to Check in Railway Build Logs

### 1. Build Phase - Look for these steps:

```
Step X/Y : COPY apps/worker/package*.json apps/worker/
Step X/Y : RUN cd apps/worker && npm install
 ---> Running in <container-id>
added 64 packages, and audited 65 packages in XXs
found 0 vulnerabilities
Step X/Y : COPY . .
```

**CRITICAL:** The `COPY . .` step should NOT show copying `apps/worker/node_modules/` because it's in `.dockerignore`.

### 2. Runtime Phase - First upload attempt:

```
✅ SUCCESS:
[Lighthouse Native] Step 1/2: Uploading...
[Lighthouse] Getting signed auth message...
[Lighthouse] Uploading apps/worker/out/dexarb_latest.jsonl with native encryption...
{ "Hash": "Qm...", "Name": "dexarb_latest.jsonl", "Size": "12345" }
[Lighthouse Native] Step 2/2: Applying access control...
✓ Access control applied: Success

❌ FAILURE (if node_modules still missing):
Error: Cannot find module '@lighthouse-web3/sdk'
```

## How to Verify node_modules Exists in Container

If you have Railway CLI:
```bash
railway run bash
cd /app/apps/worker
ls -la node_modules/@lighthouse-web3/
```

Or add this temporary debug line to `lighthouse_native_encryption.py`:
```python
import os
print(f"DEBUG: Files in {Path(__file__).parent}: {os.listdir(Path(__file__).parent)}")
print(f"DEBUG: node_modules exists: {os.path.exists(Path(__file__).parent / 'node_modules')}")
```

## Timeline Expectations

- **Now:** Railway detects commit 67a8cf6
- **+1-2 min:** Build completes with .dockerignore
- **+3 min:** Container starts, worker begins
- **+5-8 min:** First upload attempt (5 min interval)
- **Result:** Either success with CID, or same error if build cache issue

## If Error Persists

Railway might be using cached layers. Try:

1. **Force Rebuild:** In Railway dashboard → Deployments → Click "..." → "Redeploy"
2. **Check Build Timestamp:** Ensure it's AFTER 12:21:57 (your last error)
3. **Verify Commit:** Build logs should show "Building from commit 67a8cf6"

## The Root Cause (Documented)

**Problem:** Docker build installs node_modules, then `COPY . .` overwrites it
- Step 1: `npm install` creates `/app/apps/worker/node_modules/`
- Step 2: `COPY . .` copies local `apps/worker/` (no node_modules, it's gitignored)
- Step 3: Container has `/app/apps/worker/` but NO `node_modules/`

**Solution:** `.dockerignore` excludes `apps/worker/node_modules` from `COPY . .`
- Now `COPY . .` skips `apps/worker/node_modules/`
- Preserves the npm-installed dependencies
- Container has both code AND node_modules

This is a **standard Docker pattern** - always dockerignore what you build during the image creation.
