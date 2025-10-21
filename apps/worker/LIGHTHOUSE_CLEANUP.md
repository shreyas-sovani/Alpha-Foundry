# Lighthouse Auto-Cleanup

Automatic cleanup module that maintains only the latest file on Lighthouse storage.

## Features

- ✅ Keeps exactly 1 file (the latest)
- ✅ Integrates seamlessly with worker upload cycle
- ✅ Uses reliable Lighthouse CLI (`lighthouse-web3`)
- ✅ Safe: Never deletes the current file
- ✅ Atomic operations with verification
- ✅ Comprehensive logging
- ✅ Dry-run mode for testing

## Integration

The cleanup runs automatically after each successful upload in `run.py`:

```python
# After successful upload:
from lighthouse_cleanup import cleanup_lighthouse_storage

cleanup_result = cleanup_lighthouse_storage(
    api_key=settings.LIGHTHOUSE_API_KEY,
    protected_cid=new_cid,  # Protect the file we just uploaded
    dry_run=False
)

if cleanup_result["success"]:
    logger.info(f"Deleted {cleanup_result['files_deleted']} old files")
```

## Prerequisites

1. **Install Lighthouse CLI:**
   ```bash
   npm install -g @lighthouse-web3/sdk
   ```

2. **Install Python dependencies:**
   ```bash
   pip install requests
   ```

3. **Configure API key:**
   ```bash
   export LIGHTHOUSE_API_KEY="your_api_key_here"
   ```

## Manual Usage

**Dry run (safe test):**
```bash
python3 lighthouse_cleanup.py \
  --api-key "your_key" \
  --dry-run \
  --verbose
```

**Actual cleanup:**
```bash
python3 lighthouse_cleanup.py \
  --api-key "your_key" \
  --verbose
```

**Protect specific CID:**
```bash
python3 lighthouse_cleanup.py \
  --api-key "your_key" \
  --protected-cid "QmXXX..." \
  --verbose
```

## API

### Convenience Function

```python
from lighthouse_cleanup import cleanup_lighthouse_storage

result = cleanup_lighthouse_storage(
    api_key="your_key",
    protected_cid="QmXXX...",  # Optional
    dry_run=False  # Set True for testing
)

# Result dict:
{
    "success": True,
    "files_deleted": 4,
    "files_failed": 0,
    "files_remaining": 1,
    "space_saved_mb": 2.57,
    "protected_file": "QmXXX...",
    "elapsed_seconds": 1.8
}
```

### Class API

```python
from lighthouse_cleanup import LighthouseCleanup

cleanup = LighthouseCleanup(api_key="your_key")
result = cleanup.cleanup_old_files(protected_cid="QmXXX...")
```

## How It Works

1. **List files:** Fetches all files from Lighthouse API
2. **Identify latest:** Uses newest timestamp or specified CID
3. **Delete old files:** Uses CLI `lighthouse-web3 delete-file <id>`
4. **Verify:** Re-checks file count to confirm success
5. **Report:** Returns detailed results dictionary

## Safety Features

- ✅ **Never deletes protected file** (latest or specified CID)
- ✅ **Minimum threshold:** Won't delete if ≤ 1 file exists
- ✅ **Dry-run mode:** Test without actual deletion
- ✅ **Verification step:** Confirms deletion success
- ✅ **Error handling:** Graceful failures with logging
- ✅ **Atomic operations:** All-or-nothing approach

## Performance

- **Average:** ~0.3s per file deletion
- **4 files:** ~1.8 seconds total
- **100 files:** ~30 seconds total
- **Parallel:** Could be improved with concurrent deletion

## Logging

```
2025-10-21 21:04:08,614 - INFO - 📋 Found 5 files on Lighthouse
2025-10-21 21:04:08,617 - INFO - 🛡️  Protected: QmZV2F... (0.67 MB)
2025-10-21 21:04:08,617 - INFO - 🗑️  To delete: 4 files
2025-10-21 21:04:09,983 - DEBUG - ✅ Deleted: QmYSFC... (0.60 MB)
2025-10-21 21:04:10,049 - INFO - 🎉 CLEANUP COMPLETE
2025-10-21 21:04:10,049 - INFO -    Deleted: 4/4
2025-10-21 21:04:10,049 - INFO -    Space saved: 2.57 MB
```

## Troubleshooting

### CLI not found
```bash
npm install -g @lighthouse-web3/sdk
lighthouse-web3 api-key --import YOUR_KEY
```

### API key not configured
```bash
lighthouse-web3 api-key --import 7e711ba4.5db09f1a...
```

### Permission denied
```bash
sudo npm install -g @lighthouse-web3/sdk
```

## Environment Variables

```bash
LIGHTHOUSE_API_KEY=your_api_key_here  # Required
```

## Testing

```bash
# Test with dry-run
python3 lighthouse_cleanup.py --api-key "key" --dry-run

# Test with verbose logging
python3 lighthouse_cleanup.py --api-key "key" --verbose

# Test protecting specific CID
python3 lighthouse_cleanup.py --api-key "key" --protected-cid "QmXXX..."
```

## Production Usage

The module is automatically integrated into the worker's upload cycle:
- Runs after each successful upload
- Deletes all old files
- Keeps only the latest upload
- Logs results for monitoring

**Result:** Always exactly 1 file on Lighthouse, minimizing storage costs!
