# Lighthouse File Protection Configuration

## Overview

The Lighthouse cleanup system has been configured to permanently protect specific CIDs from deletion while automatically cleaning up old files.

## Protected Files

### Permanent Protection (Hardcoded)

The following CIDs are **permanently protected** and will **NEVER be deleted**:

1. `bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4`
2. `bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy`

These CIDs are hardcoded in the `LighthouseCleanup` class as `PERMANENT_PROTECTED_CIDS`.

### Dynamic Protection

In addition to the permanent CIDs, the system also protects:

- **Latest uploaded file**: The most recent CID stored in `metadata.json` (passed via `protected_cid` parameter)
- **Additional CIDs**: Optional CIDs can be passed during initialization via the `additional_protected_cids` parameter

## Implementation Details

### Location

File: `/apps/worker/lighthouse_cleanup.py`

### Key Components

```python
class LighthouseCleanup:
    # Permanently protected CIDs that should NEVER be deleted
    PERMANENT_PROTECTED_CIDS = {
        "bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4",
        "bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy"
    }
```

### How It Works

1. **Initialization**: When the cleanup service starts, it loads the permanent CIDs into a protected set
2. **File Listing**: Fetches all files from Lighthouse storage
3. **Protection Logic**: Identifies files to keep:
   - Files matching `PERMANENT_PROTECTED_CIDS`
   - The latest CID from `metadata.json`
   - Any additional CIDs specified
4. **Cleanup**: Deletes only files that are NOT in the protected set
5. **Logging**: Provides detailed logs showing which files are protected and why

### Example Log Output

```
🛡️  Permanent protection enabled for 2 CIDs
📋 Found 15 files on Lighthouse
🛡️  Protected files: 3
     • bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iov... (5.23 MB) [PERMANENT]
     • bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s... (1.45 MB) [PERMANENT]
     • QmXXXnewlatestupload... (8.12 MB) [LATEST]
🗑️  Files to delete: 12
```

## Configuration Changes

### Before (Old Behavior)

- Protected only 1 file (the latest)
- All other files were deleted
- No way to permanently protect specific files

### After (New Behavior)

- Protects 2 permanent CIDs (hardcoded)
- Protects the latest uploaded file
- Optional: Can protect additional CIDs
- Only deletes unprotected files

## Testing

### Dry Run Mode

You can test the cleanup logic without deleting files:

```python
from lighthouse_cleanup import cleanup_lighthouse_storage

result = cleanup_lighthouse_storage(
    api_key="your_api_key",
    protected_cid="latest_cid",
    dry_run=True  # Won't actually delete files
)

print(f"Would delete: {result['files_deleted']} files")
print(f"Protected: {result['protected_files']}")
```

### Manual Testing

```bash
cd /apps/worker
python lighthouse_cleanup.py --api-key "YOUR_KEY" --protected-cid "LATEST_CID" --dry-run --verbose
```

## Integration with Worker

The cleanup runs automatically after each successful upload in `run.py`:

```python
cleanup_result = cleanup_lighthouse_storage(
    api_key=settings.LIGHTHOUSE_API_KEY,
    protected_cid=new_cid,  # Latest uploaded CID
    dry_run=False
)
```

The permanent CIDs are automatically protected on every cleanup cycle.

## Modifying Protected CIDs

### To Add More Permanent CIDs

Edit `/apps/worker/lighthouse_cleanup.py`:

```python
PERMANENT_PROTECTED_CIDS = {
    "bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4",
    "bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy",
    "your_new_cid_here"  # Add new CIDs here
}
```

### To Add Temporary Protection

Pass additional CIDs during initialization:

```python
cleanup = LighthouseCleanup(
    api_key=api_key,
    additional_protected_cids=["cid1", "cid2"]
)
```

## Best Practices

1. **Permanent CIDs**: Only add CIDs to `PERMANENT_PROTECTED_CIDS` that must never be deleted (e.g., critical data, documentation, configuration files)

2. **Code Review**: Any changes to `PERMANENT_PROTECTED_CIDS` should be reviewed and documented

3. **Monitoring**: Check logs regularly to ensure protected files are not being deleted

4. **Testing**: Always test with `dry_run=True` before deploying protection changes

5. **Documentation**: Document why each permanent CID is protected

## Safety Features

- **Multiple Protection Layers**: Files can be protected via multiple mechanisms
- **No Duplicates**: Uses sets internally to avoid duplicate CIDs
- **Fallback**: If protected CID not found, uses newest file
- **Logging**: Comprehensive logging of all protection decisions
- **Dry Run**: Test mode available for safe testing

## Troubleshooting

### Protected File Getting Deleted

Check logs for:
- CID typos in `PERMANENT_PROTECTED_CIDS`
- Proper CID format (should match exactly as stored on Lighthouse)

### Too Many Files Remaining

- Check if CIDs are correct
- Verify cleanup is running (check logs)
- Ensure Lighthouse CLI is installed and configured

### File Not Found Warning

```
⚠️  Protected CID not found: xxx, using newest file
```

This means the specified CID doesn't exist on Lighthouse. The system will fallback to protecting the newest file.

## Change Log

### 2025-10-22: Multiple CID Protection

- Added `PERMANENT_PROTECTED_CIDS` class variable
- Modified `identify_files_to_delete()` to return lists instead of single file
- Updated protection logic to handle multiple protected CIDs
- Enhanced logging to show protection reasons
- Updated return format from `protected_file` to `protected_files`

## Related Files

- `/apps/worker/lighthouse_cleanup.py` - Main cleanup logic
- `/apps/worker/run.py` - Integration with worker cycle
- `/apps/worker/out/metadata.json` - Contains latest CID
