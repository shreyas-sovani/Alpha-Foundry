# 🔧 Lighthouse Upload Timeout Fix

## Problem Discovered

On Railway deployment, Lighthouse uploads were **hanging indefinitely**, blocking the worker cycle:

```
2025-10-21 12:02:38,057 [INFO] Uploading dexarb_latest.jsonl.enc (80,655 bytes)...
[Upload hangs - no completion message]
[Worker cycle blocked for 15+ seconds]
```

### Root Cause
The official Lighthouse Python SDK's `upload()` method is **synchronous and blocking**. Even though we wrapped it in `asyncio.run_in_executor`, the underlying network call was timing out without proper error handling.

## Solution Implemented

### 1. Added Timeout Protection
```python
result = await asyncio.wait_for(
    loop.run_in_executor(...),
    timeout=settings.LIGHTHOUSE_UPLOAD_TIMEOUT  # Default: 60s
)
```

### 2. Better Error Handling
```python
except asyncio.TimeoutError:
    logger.error(f"❌ Lighthouse upload timed out after {duration}s")
    logger.error(f"   Tip: Increase LIGHTHOUSE_UPLOAD_TIMEOUT or disable with LIGHTHOUSE_ENABLE_UPLOAD=false")
    return None
except Exception as e:
    logger.error(f"❌ Lighthouse upload failed: {e}")
    return None
```

### 3. Made Upload Optional (Default: Disabled)
```python
LIGHTHOUSE_ENABLE_UPLOAD: bool = False  # Disabled by default to avoid blocking
```

### 4. Configurable Timeout
```python
LIGHTHOUSE_UPLOAD_TIMEOUT: int = 60  # Seconds
```

## New Environment Variables

### Required to Enable Upload:
```bash
LIGHTHOUSE_ENABLE_UPLOAD=true
LIGHTHOUSE_API_KEY=your_key_here
```

### Optional Configuration:
```bash
LIGHTHOUSE_UPLOAD_TIMEOUT=120  # Increase if uploads are slow (default: 60)
```

## Behavior Now

### When LIGHTHOUSE_ENABLE_UPLOAD=false (default):
```
✓ Updated metadata: 106 rows
[No upload - skipped]
✓ Updated preview: ...
```

### When LIGHTHOUSE_ENABLE_UPLOAD=true:
```
✓ Updated metadata: 106 rows
📤 Uploading dexarb_latest.jsonl to Lighthouse (timeout: 60s)...
Step 1/2: Encrypting dexarb_latest.jsonl...
✓ Encrypted: ... (0.03s)
Step 2/2: Uploading dexarb_latest.jsonl.enc...
```

**Then either:**
```
✅ Lighthouse upload successful in 45.2s
   CID: QmXxxx...
✓ Lighthouse CID: QmXxxx...
```

**Or if timeout/error:**
```
❌ Lighthouse upload timed out after 60.1s
   Tip: Increase LIGHTHOUSE_UPLOAD_TIMEOUT or disable with LIGHTHOUSE_ENABLE_UPLOAD=false
```

## Why Disabled By Default?

1. **Prevents worker blocking** - If Lighthouse API is slow/down, worker continues
2. **Faster development** - Local testing doesn't require Lighthouse setup
3. **Explicit opt-in** - Users consciously enable uploads
4. **Graceful degradation** - Worker works without Lighthouse

## How to Enable on Railway

### Option 1: Enable with Default Timeout (60s)
```bash
railway variables set LIGHTHOUSE_ENABLE_UPLOAD=true
railway variables set LIGHTHOUSE_API_KEY=your_key_here
```

### Option 2: Enable with Custom Timeout (e.g., 120s for slow networks)
```bash
railway variables set LIGHTHOUSE_ENABLE_UPLOAD=true
railway variables set LIGHTHOUSE_API_KEY=your_key_here
railway variables set LIGHTHOUSE_UPLOAD_TIMEOUT=120
```

## Testing Recommendations

### 1. Local Test (No Upload)
```bash
# Default - upload disabled
LIGHTHOUSE_ENABLE_UPLOAD=false python apps/worker/run.py
```

### 2. Local Test (With Upload)
```bash
# May fail on network but won't block worker
LIGHTHOUSE_ENABLE_UPLOAD=true \
LIGHTHOUSE_API_KEY=xxx \
LIGHTHOUSE_UPLOAD_TIMEOUT=30 \
python apps/worker/run.py
```

### 3. Railway Test (Staged Rollout)
1. Deploy with `LIGHTHOUSE_ENABLE_UPLOAD=false` (safe)
2. Monitor logs to ensure worker is healthy
3. Enable upload: `railway variables set LIGHTHOUSE_ENABLE_UPLOAD=true`
4. Monitor for timeout errors
5. If timeouts occur, increase: `railway variables set LIGHTHOUSE_UPLOAD_TIMEOUT=120`

## Monitoring

### Success Indicators:
```bash
railway logs | grep "Lighthouse upload successful"
```

### Timeout Detection:
```bash
railway logs | grep "Lighthouse upload timed out"
```

### If Timeouts Occur:
1. **Increase timeout**: `LIGHTHOUSE_UPLOAD_TIMEOUT=120` (or higher)
2. **Check Lighthouse status**: https://status.lighthouse.storage
3. **Temporary disable**: `LIGHTHOUSE_ENABLE_UPLOAD=false`
4. **Check network**: Railway → Lighthouse API connectivity

## Files Modified

1. `apps/worker/settings.py`
   - Changed default: `LIGHTHOUSE_ENABLE_UPLOAD = False`
   - Added: `LIGHTHOUSE_UPLOAD_TIMEOUT = 60`
   - Added timeout to startup logs

2. `apps/worker/run.py`
   - Added `asyncio.wait_for()` wrapper with timeout
   - Better error handling for timeouts
   - More descriptive error messages with tips

## Benefits

✅ **Worker never blocks** - Timeout protection  
✅ **Graceful failure** - Continues on upload errors  
✅ **Explicit opt-in** - Upload disabled by default  
✅ **Configurable** - Adjust timeout per environment  
✅ **Better logging** - Clear error messages with solutions  
✅ **Production-ready** - Safe for Railway deployment  

## Next Steps

1. **Push these changes**:
   ```bash
   git add -A
   git commit -m "fix: add timeout protection for Lighthouse uploads"
   git push origin main
   ```

2. **Railway will auto-deploy** with upload disabled by default

3. **Enable when ready**:
   ```bash
   railway variables set LIGHTHOUSE_ENABLE_UPLOAD=true
   ```

4. **Monitor logs** for success/timeout messages

---

**Status**: ✅ Fixed - Upload protected with timeout  
**Default**: Upload disabled (safe)  
**Recommendation**: Enable with `LIGHTHOUSE_ENABLE_UPLOAD=true` after deployment stabilizes
