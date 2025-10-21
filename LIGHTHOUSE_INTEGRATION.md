# Lighthouse Integration for DEX Data Pipeline

This integration adds **decentralized file encryption and IPFS/Filecoin upload** to your DEX arbitrage data pipeline, making it eligible for the ETHOnline/Lighthouse challenge.

## Features

- ✅ **Client-side AES-256-GCM encryption** for dexarb_latest.jsonl
- ✅ **IPFS/Filecoin upload** via Lighthouse API
- ✅ **CID verification** via Lighthouse gateway
- ✅ **Atomic metadata.json updates** with latest CID
- ✅ **Non-breaking**: All existing endpoints remain functional

## Quick Start

### 1. Get Lighthouse API Key

1. Visit [https://files.lighthouse.storage/](https://files.lighthouse.storage/)
2. Connect your wallet
3. Generate an API key
4. Copy the key (you'll need it in step 2)

### 2. Set Environment Variables

```bash
# Required
export LIGHTHOUSE_API_KEY="your_lighthouse_api_key_here"

# Optional (defaults to LIGHTHOUSE_API_KEY if not set)
export LIGHTHOUSE_PASSWORD="custom_encryption_password"
```

**Security Note**: Never commit your API key to git. Add it to `.env.local` or use Railway secrets.

### 3. Verify Installation

```bash
# Check dependencies
python -c "import cryptography; import httpx; print('✓ Dependencies OK')"

# Validate configuration
python scripts/lighthouse_upload.py --help
```

### 4. Manual Upload (Testing)

```bash
# Encrypt and upload dexarb_latest.jsonl
python scripts/lighthouse_upload.py --verify

# With custom password
python scripts/lighthouse_upload.py --verify --password "my_secure_password"
```

### 5. Check Results

After successful upload, you should see:

```
✅ PASS: Lighthouse encryption/upload live, metadata CID synced

Next steps:
1. View file in explorer: Qm...
   https://gateway.lighthouse.storage/ipfs/Qm...
2. Check metadata.json: apps/worker/out/metadata.json
3. Encrypted file saved: apps/worker/out/dexarb_latest.jsonl.enc
```

## Integration with Worker

### Option A: Manual Periodic Uploads

Run the script manually or via cron:

```bash
# Every hour
0 * * * * cd /path/to/af_hosted && /path/to/.venv/bin/python scripts/lighthouse_upload.py --verify
```

### Option B: Automatic Uploads in Worker Loop

Add to `run.py` (in the main cycle):

```python
from lighthouse_integration import encrypt_and_upload_rolling_data, LighthouseError

# After update_metadata() call
if settings.LIGHTHOUSE_ENABLED:
    try:
        lighthouse_result = encrypt_and_upload_rolling_data(
            jsonl_path=jsonl_path,
            metadata_path=metadata_path,
            api_key=settings.LIGHTHOUSE_API_KEY,
            password=settings.LIGHTHOUSE_PASSWORD,
            verify=True,
        )
        logger.info(f"✓ Lighthouse CID: {lighthouse_result['cid']}")
    except LighthouseError as e:
        logger.error(f"Lighthouse upload failed: {e}")
        # Continue without failing the cycle
```

Add to `settings.py`:

```python
# Lighthouse Configuration
LIGHTHOUSE_ENABLED: bool = False
LIGHTHOUSE_API_KEY: Optional[str] = None
LIGHTHOUSE_PASSWORD: Optional[str] = None
```

## API Reference

### `encrypt_and_upload_rolling_data()`

Main entry point for Lighthouse integration.

```python
from lighthouse_integration import encrypt_and_upload_rolling_data

result = encrypt_and_upload_rolling_data(
    jsonl_path=Path("apps/worker/out/dexarb_latest.jsonl"),
    metadata_path=Path("apps/worker/out/metadata.json"),
    api_key="your_api_key",
    password="optional_password",  # Defaults to api_key
    verify=True,  # Verify CID accessibility
)

print(f"CID: {result['cid']}")
print(f"Gateway: https://gateway.lighthouse.storage/ipfs/{result['cid']}")
```

**Returns:**

```python
{
    "cid": "QmXXX...",  # IPFS CID
    "encrypted_file": "apps/worker/out/dexarb_latest.jsonl.enc",
    "verified": True,  # Whether CID is accessible
    "encryption_stats": {
        "original_size": 123456,
        "encrypted_size": 123500,
        "encryption_time": 0.15,
        "sha256_original": "abc123...",
        "sha256_encrypted": "def456...",
    },
    "upload_stats": {
        "cid": "QmXXX...",
        "size": 123500,
        "upload_time": 2.5,
    },
    "metadata_diff": {
        "before": {...},
        "after": {...},
    },
    "total_time": 2.65,
}
```

### `LighthouseClient`

Low-level client for custom workflows.

```python
from lighthouse_integration import LighthouseClient

client = LighthouseClient(api_key="your_api_key")

# Encrypt file
encryption_stats = client.encrypt_file(
    input_path=Path("data.jsonl"),
    output_path=Path("data.jsonl.enc"),
)

# Upload file
upload_result = client.upload_file(
    file_path=Path("data.jsonl.enc"),
)

# Verify CID
verified = client.verify_cid(upload_result["cid"])

client.close()
```

## Metadata.json Updates

After successful upload, `metadata.json` is atomically updated with:

```json
{
  "latest_cid": "QmXXX...",
  "lighthouse_gateway": "https://gateway.lighthouse.storage/ipfs/QmXXX...",
  "encryption": {
    "enabled": true,
    "algorithm": "AES-256-GCM",
    "encrypted_file": "dexarb_latest.jsonl.enc",
    "encrypted_size": 123500,
    "original_size": 123456,
    "sha256_encrypted": "def456...",
    "sha256_original": "abc123..."
  },
  "last_lighthouse_upload": "2025-10-21T10:45:00Z",
  ... // existing fields preserved
}
```

## Security

### Encryption

- **Algorithm**: AES-256-GCM (AEAD cipher)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt**: 16-byte random salt per file
- **Nonce**: 12-byte random nonce per encryption

### Key Management

- API key is never stored in code or version control
- Use environment variables or secure secret management
- For production, consider using separate encryption passwords

### Decryption

To decrypt a file:

```python
from lighthouse_integration import decrypt_file

decrypt_file(
    encrypted_path=Path("dexarb_latest.jsonl.enc"),
    output_path=Path("dexarb_latest_decrypted.jsonl"),
    password="your_password",  # Must match encryption password
)
```

## Troubleshooting

### Error: "LIGHTHOUSE_API_KEY is required"

**Solution**: Set the environment variable:

```bash
export LIGHTHOUSE_API_KEY="your_key_here"
```

### Error: "File not found: dexarb_latest.jsonl"

**Solution**: Ensure the worker has run at least once to generate the file:

```bash
ls -lh apps/worker/out/dexarb_latest.jsonl
```

### Error: "Upload failed (HTTP 401)"

**Solution**: API key is invalid. Generate a new one at [https://files.lighthouse.storage/](https://files.lighthouse.storage/)

### Warning: "CID not immediately accessible"

**Solution**: IPFS propagation can take 10-30 seconds. Try again:

```bash
curl -I https://gateway.lighthouse.storage/ipfs/YOUR_CID_HERE
```

### Error: "Decryption failed"

**Solution**: Password doesn't match. Use the same password you used for encryption.

## Testing

### Unit Tests

```bash
# Test encryption
python -c "
from lighthouse_integration import LighthouseClient
from pathlib import Path
import tempfile

client = LighthouseClient(api_key='test_key')
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write('Hello Lighthouse!')
    temp_path = Path(f.name)

encrypted_path = temp_path.with_suffix('.txt.enc')
stats = client.encrypt_file(temp_path, encrypted_path)
print(f'✓ Encrypted: {stats}')
"
```

### Integration Test

```bash
# Full workflow test (requires valid API key)
export LIGHTHOUSE_API_KEY="your_key"
python scripts/lighthouse_upload.py --verify --jsonl test_data.jsonl
```

## ETHOnline Challenge Submission

This integration demonstrates:

1. ✅ **Decentralized Storage**: IPFS/Filecoin via Lighthouse
2. ✅ **Encryption**: AES-256-GCM client-side encryption
3. ✅ **Data Integrity**: SHA-256 checksums for verification
4. ✅ **Persistent CIDs**: Immutable content addressing
5. ✅ **Gateway Access**: Public retrieval via Lighthouse gateway
6. ✅ **Metadata Tracking**: On-chain compatible CID storage

### Submission Checklist

- [ ] API key generated and configured
- [ ] At least one successful upload with verified CID
- [ ] `metadata.json` contains `latest_cid` field
- [ ] Encrypted file accessible via Lighthouse gateway
- [ ] Documentation complete (this README)
- [ ] Live demo available (endpoints + agent working)

## Resources

- **Lighthouse Docs**: [https://docs.lighthouse.storage/](https://docs.lighthouse.storage/)
- **Quick Start**: [https://docs.lighthouse.storage/lighthouse-1/quick-start](https://docs.lighthouse.storage/lighthouse-1/quick-start)
- **SDK Reference**: [@lighthouse-web3/sdk](https://www.npmjs.com/package/@lighthouse-web3/sdk)
- **Explorer**: [https://gateway.lighthouse.storage/](https://gateway.lighthouse.storage/)
- **Status**: [https://status.lighthouse.storage/](https://status.lighthouse.storage/)

## License

Same as parent project.
