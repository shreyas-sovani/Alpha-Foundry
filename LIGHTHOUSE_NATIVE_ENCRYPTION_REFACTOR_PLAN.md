# Lighthouse Native Encryption with ERC20 Token-Gating - Implementation Plan

## Executive Summary

**Current State:** Backend uses custom AES-256-GCM encryption → uploads encrypted file to Lighthouse → NO access control  
**Target State:** Backend uses Lighthouse native `uploadEncrypted()` → applies ERC20 access control via `applyAccessCondition()` → enforces token-gating

**Problem:** Frontend's `lighthouse.fetchEncryptionKey(cid, address, signature)` fails with "cid not found" because the CID has no Lighthouse access control configured.

**Solution:** Refactor Python backend to use Lighthouse's native encryption system with automated ERC20 token-gating.

---

## 1. Technical Architecture

### Current Flow (BROKEN for Token-Gating)
```
1. Python custom AES-256-GCM encryption
   └─> lighthouse_sdk_integration.py::encrypt_file()
       ├─> PBKDF2 key derivation (100k iterations)
       ├─> 32-byte salt + 12-byte IV
       └─> AES-GCM encryption

2. Upload encrypted file to Lighthouse
   └─> lighthouse.upload(encrypted_file_path, tag)
       └─> POST https://upload.lighthouse.storage/api/v0/add
           └─> Returns CID (e.g., QmWxabyCrJnxiVvhcXSj8G9eZNAHTj8JtxdkCBB3iy2DZd)

3. Update metadata.json
   └─> Records CID, encryption="Custom AES-256-GCM", no access control info

4. Frontend decryption attempt (FAILS)
   └─> lighthouse.fetchEncryptionKey(cid, wallet_address, signature)
       └─> 400 Bad Request: "cid not found"
       └─> WHY: Lighthouse has no encryption key shards stored
       └─> WHY: No access control conditions configured
```

### Target Flow (WORKING Token-Gating)
```
1. Python calls Lighthouse native encryption
   └─> lighthouse.uploadEncrypted(file_path, apiKey, publicKey, signedMessage)
       ├─> Lighthouse Kavach SDK handles encryption
       ├─> BLS cryptography with 5-shard key distribution
       ├─> Stores key shards on Lighthouse nodes
       └─> Returns CID with encryption metadata

2. Immediately apply ERC20 access control
   └─> lighthouse.applyAccessCondition(publicKey, cid, signedMessage, conditions, aggregator)
       ├─> conditions = [{
       │     id: 1,
       │     chain: "Sepolia",
       │     method: "balanceOf",
       │     standardContractType: "ERC20",
       │     contractAddress: "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
       │     returnValueTest: { comparator: ">=", value: "1000000000000000000" },
       │     parameters: [":userAddress"]
       │   }]
       ├─> aggregator = "([1])"
       └─> chainType = "evm"

3. Update metadata.json
   └─> Records CID, encryption="Lighthouse Native", access_control={...}, contract_address, chain_id

4. Frontend decryption (WORKS)
   └─> lighthouse.fetchEncryptionKey(cid, wallet_address, signature)
       ├─> Lighthouse checks ERC20 balance on Sepolia
       ├─> If balance >= 1.0 DADC: Return encryption key
       ├─> If balance < 1.0 DADC: Reject with 403 Forbidden
       └─> Frontend decrypts with key
```

---

## 2. Code Changes Required

### 2.1 Python Lighthouse SDK Integration

**Problem:** Python `lighthouseweb3` package doesn't have direct `uploadEncrypted()` method.

**Solution:** Use JavaScript Lighthouse SDK via subprocess or REST API calls.

#### Option A: Direct REST API (RECOMMENDED)
```python
# apps/worker/lighthouse_native_encryption.py (NEW FILE)

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

class LighthouseNativeEncryption:
    """
    Lighthouse native encryption with ERC20 token-gating.
    Uses Node.js @lighthouse-web3/sdk via subprocess.
    """
    
    def __init__(self, api_key: str, private_key: str):
        self.api_key = api_key
        self.private_key = private_key
        self.wallet_address = self._derive_address()
    
    def _derive_address(self) -> str:
        """Derive Ethereum address from private key."""
        # Use ethers.js or web3.py
        from eth_account import Account
        account = Account.from_key(self.private_key)
        return account.address
    
    def _get_signed_message(self) -> str:
        """
        Get authentication message from Lighthouse and sign it.
        
        Flow:
        1. GET https://api.lighthouse.storage/api/auth/get_message?publicKey={address}
        2. Sign message with private key
        3. Return signed message
        """
        import requests
        from eth_account.messages import encode_defunct
        from eth_account import Account
        
        # Get message to sign
        response = requests.get(
            f"https://api.lighthouse.storage/api/auth/get_message?publicKey={self.wallet_address}"
        )
        response.raise_for_status()
        message = response.json()
        
        # Sign message
        account = Account.from_key(self.private_key)
        message_hash = encode_defunct(text=message)
        signed = account.sign_message(message_hash)
        return signed.signature.hex()
    
    def upload_encrypted(self, file_path: str, tag: str = "") -> Dict[str, Any]:
        """
        Upload file with Lighthouse native encryption.
        
        Uses Node.js @lighthouse-web3/sdk subprocess.
        
        Returns:
            {
                "cid": "QmXXX...",
                "name": "file.jsonl",
                "size": "12345"
            }
        """
        # Create temp Node.js script
        script_content = """
const lighthouse = require('@lighthouse-web3/sdk');
const fs = require('fs');

async function uploadEncrypted() {
    const filePath = process.argv[2];
    const apiKey = process.argv[3];
    const publicKey = process.argv[4];
    const signedMessage = process.argv[5];
    
    try {
        const response = await lighthouse.uploadEncrypted(
            filePath,
            apiKey,
            publicKey,
            signedMessage
        );
        console.log(JSON.stringify(response.data[0]));
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify({error: error.message}));
        process.exit(1);
    }
}

uploadEncrypted();
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            signed_message = self._get_signed_message()
            
            # Run Node.js script
            result = subprocess.run(
                [
                    'node',
                    script_path,
                    file_path,
                    self.api_key,
                    self.wallet_address,
                    signed_message
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if result.returncode != 0:
                raise Exception(f"Upload failed: {result.stderr}")
            
            upload_result = json.loads(result.stdout)
            
            if 'error' in upload_result:
                raise Exception(f"Upload error: {upload_result['error']}")
            
            return {
                "cid": upload_result["Hash"],
                "name": upload_result["Name"],
                "size": upload_result["Size"]
            }
        finally:
            Path(script_path).unlink(missing_ok=True)
    
    def apply_access_control(
        self,
        cid: str,
        contract_address: str,
        chain: str,
        min_balance_wei: int
    ) -> Dict[str, Any]:
        """
        Apply ERC20 token-gating to uploaded CID.
        
        Args:
            cid: Lighthouse CID
            contract_address: ERC20 token contract (e.g., DataCoin)
            chain: Chain name (e.g., "Sepolia")
            min_balance_wei: Minimum balance in wei (1 DADC = 1e18)
        
        Returns:
            {"status": "Success", "cid": "QmXXX..."}
        """
        script_content = """
const lighthouse = require('@lighthouse-web3/sdk');

async function applyAccessControl() {
    const publicKey = process.argv[2];
    const cid = process.argv[3];
    const signedMessage = process.argv[4];
    const conditions = JSON.parse(process.argv[5]);
    const aggregator = process.argv[6];
    
    try {
        const response = await lighthouse.applyAccessCondition(
            publicKey,
            cid,
            signedMessage,
            conditions,
            aggregator
        );
        console.log(JSON.stringify(response.data));
        process.exit(0);
    } catch (error) {
        console.error(JSON.stringify({error: error.message}));
        process.exit(1);
    }
}

applyAccessControl();
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            signed_message = self._get_signed_message()
            
            # Build access control conditions
            conditions = [{
                "id": 1,
                "chain": chain,
                "method": "balanceOf",
                "standardContractType": "ERC20",
                "contractAddress": contract_address,
                "returnValueTest": {
                    "comparator": ">=",
                    "value": str(min_balance_wei)
                },
                "parameters": [":userAddress"]
            }]
            
            aggregator = "([1])"
            
            # Run Node.js script
            result = subprocess.run(
                [
                    'node',
                    script_path,
                    self.wallet_address,
                    cid,
                    signed_message,
                    json.dumps(conditions),
                    aggregator
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise Exception(f"Access control failed: {result.stderr}")
            
            access_result = json.loads(result.stdout)
            
            if 'error' in access_result:
                raise Exception(f"Access control error: {access_result['error']}")
            
            return access_result
        finally:
            Path(script_path).unlink(missing_ok=True)
    
    def encrypt_and_upload_with_gating(
        self,
        file_path: str,
        tag: str,
        datacoin_address: str,
        chain: str = "Sepolia",
        min_balance_dadc: float = 1.0
    ) -> Dict[str, Any]:
        """
        Complete flow: Upload with encryption + Apply token-gating.
        
        Args:
            file_path: Path to file to upload
            tag: Upload tag
            datacoin_address: DataCoin ERC20 contract address
            chain: Blockchain name
            min_balance_dadc: Minimum token balance (in DADC, not wei)
        
        Returns:
            {
                "cid": "QmXXX...",
                "name": "file.jsonl",
                "size": "12345",
                "encryption": "Lighthouse Native",
                "access_control": {
                    "status": "Success",
                    "contract": "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
                    "chain": "Sepolia",
                    "min_balance": "1.0 DADC"
                }
            }
        """
        # Step 1: Upload with native encryption
        print(f"[1/2] Uploading {file_path} with Lighthouse native encryption...")
        upload_result = self.upload_encrypted(file_path, tag)
        cid = upload_result["cid"]
        print(f"✓ Uploaded: {cid}")
        
        # Step 2: Apply ERC20 token-gating
        print(f"[2/2] Applying ERC20 token-gating...")
        min_balance_wei = int(min_balance_dadc * 1e18)
        
        access_result = self.apply_access_control(
            cid=cid,
            contract_address=datacoin_address,
            chain=chain,
            min_balance_wei=min_balance_wei
        )
        print(f"✓ Access control applied: {access_result['status']}")
        
        return {
            "cid": cid,
            "name": upload_result["name"],
            "size": upload_result["size"],
            "encryption": "Lighthouse Native",
            "access_control": {
                "status": access_result["status"],
                "contract": datacoin_address,
                "chain": chain,
                "min_balance": f"{min_balance_dadc} DADC"
            }
        }
```

#### Option B: Python-only via REST API (ALTERNATIVE)
```python
# apps/worker/lighthouse_native_encryption_rest.py (ALTERNATIVE)

import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from typing import Dict, Any

class LighthouseNativeEncryptionREST:
    """
    Lighthouse native encryption via direct REST API calls.
    No Node.js dependency.
    """
    
    def __init__(self, api_key: str, private_key: str):
        self.api_key = api_key
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.wallet_address = self.account.address
        self.base_url = "https://upload.lighthouse.storage"
        self.api_url = "https://api.lighthouse.storage"
        self.encryption_url = "https://encryption.lighthouse.storage"
    
    def _sign_auth_message(self) -> str:
        """Get and sign Lighthouse auth message."""
        response = requests.get(
            f"{self.api_url}/api/auth/get_message",
            params={"publicKey": self.wallet_address}
        )
        response.raise_for_status()
        message = response.json()
        
        message_hash = encode_defunct(text=message)
        signed = self.account.sign_message(message_hash)
        return signed.signature.hex()
    
    def upload_encrypted(self, file_path: str) -> Dict[str, Any]:
        """
        Upload file with encryption via REST API.
        
        NOTE: This requires implementing Kavach encryption in Python
        or using the Lighthouse upload endpoint with Encryption header.
        """
        signed_message = self._sign_auth_message()
        
        # Upload with encryption flag
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Encryption': 'true'
            }
            
            response = requests.post(
                f"{self.base_url}/api/v0/add",
                files=files,
                headers=headers
            )
            response.raise_for_status()
            
            upload_data = response.json()
            
            # Save encryption shards (requires Kavach SDK)
            # This is complex - Option A with Node.js is recommended
            
            return {
                "cid": upload_data[0]["Hash"],
                "name": upload_data[0]["Name"],
                "size": upload_data[0]["Size"]
            }
    
    def apply_access_control(
        self,
        cid: str,
        conditions: list,
        aggregator: str = "([1])"
    ) -> Dict[str, Any]:
        """Apply access conditions via REST API."""
        signed_message = self._sign_auth_message()
        
        response = requests.post(
            f"{self.encryption_url}/api/accessControl/apply",
            json={
                "publicKey": self.wallet_address,
                "cid": cid,
                "signedMessage": signed_message,
                "conditions": conditions,
                "aggregator": aggregator,
                "chainType": "evm"
            }
        )
        response.raise_for_status()
        
        return response.json()
```

### 2.2 Integration with Worker

**File:** `apps/worker/run.py`

```python
# BEFORE (Current - Custom AES)
async def upload_to_lighthouse_and_cleanup(
    jsonl_path, metadata_path, settings, last_upload_time
):
    # ... existing code ...
    
    result = await loop.run_in_executor(
        None,
        lambda: lighthouse.encrypt_and_upload(  # ← CUSTOM AES
            input_path=jsonl_path,
            tag=f"dexarb_{settings.NETWORK_LABEL}",
            keep_encrypted=False
        )
    )
    
    # Update metadata
    metadata["current_cid"] = result["upload"]["cid"]
    metadata["encryption"] = "Custom AES-256-GCM"  # ← NO ACCESS CONTROL
    # ... rest ...


# AFTER (Target - Lighthouse Native)
async def upload_to_lighthouse_and_cleanup(
    jsonl_path, metadata_path, settings, last_upload_time
):
    from lighthouse_native_encryption import LighthouseNativeEncryption
    
    # Initialize Lighthouse native encryption
    lighthouse_native = LighthouseNativeEncryption(
        api_key=settings.LIGHTHOUSE_API_KEY,
        private_key=settings.LIGHTHOUSE_WALLET_PRIVATE_KEY  # NEW SETTING
    )
    
    # Upload with native encryption + ERC20 gating
    result = await loop.run_in_executor(
        None,
        lambda: lighthouse_native.encrypt_and_upload_with_gating(
            file_path=str(jsonl_path),
            tag=f"dexarb_{settings.NETWORK_LABEL}",
            datacoin_address=settings.DATACOIN_CONTRACT_ADDRESS,
            chain="Sepolia",
            min_balance_dadc=1.0
        )
    )
    
    # Update metadata with access control info
    metadata["current_cid"] = result["cid"]
    metadata["encryption"] = "Lighthouse Native"
    metadata["access_control"] = {
        "contract": result["access_control"]["contract"],
        "chain": result["access_control"]["chain"],
        "min_balance": result["access_control"]["min_balance"],
        "applied_at": datetime.now().isoformat()
    }
    
    # ... rest of cleanup logic ...
```

### 2.3 Settings Configuration

**File:** `apps/worker/settings.py`

```python
# ADD NEW SETTINGS
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Lighthouse Native Encryption
    LIGHTHOUSE_API_KEY: str = "7e711ba4.5db09f1a785145159ab740254e63f070"
    LIGHTHOUSE_WALLET_PRIVATE_KEY: str  # NEW - Required for signing
    
    # DataCoin ERC20 Gating
    DATACOIN_CONTRACT_ADDRESS: str = "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC"
    DATACOIN_CHAIN: str = "Sepolia"
    DATACOIN_MIN_BALANCE: float = 1.0  # DADC tokens
    
    # ... rest ...
```

### 2.4 Metadata Schema Update

**File:** `metadata.json`

```json
{
  "current_cid": "QmNewCIDWithAccessControl...",
  "last_upload": "2025-01-21T02:30:00Z",
  "row_count": 180,
  "encryption": "Lighthouse Native",
  "access_control": {
    "contract": "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
    "chain": "Sepolia",
    "chain_id": 11155111,
    "min_balance": "1.0 DADC",
    "applied_at": "2025-01-21T02:30:15Z"
  },
  "gateway_url": "https://gateway.lighthouse.storage/ipfs/QmNewCID...",
  "file_size": 45678,
  "network": "ethereum"
}
```

---

## 3. Implementation Steps

### Phase 1: Preparation (No Breaking Changes)
1. ✅ Create `lighthouse_native_encryption.py` module
2. ✅ Add Node.js subprocess integration for `uploadEncrypted()`
3. ✅ Add `applyAccessCondition()` integration
4. ✅ Add unit tests for new module
5. ✅ Test encryption flow locally without affecting production

### Phase 2: Settings & Configuration
1. ✅ Add `LIGHTHOUSE_WALLET_PRIVATE_KEY` to Railway environment variables
2. ✅ Update `settings.py` with new DataCoin gating settings
3. ✅ Verify Node.js and `@lighthouse-web3/sdk` available in Railway container
4. ✅ Update `requirements.txt` with `eth-account`, `web3` dependencies

### Phase 3: Worker Integration
1. ✅ Update `run.py::upload_to_lighthouse_and_cleanup()` 
2. ✅ Keep fallback to old `lighthouse_sdk_integration` if native encryption fails
3. ✅ Update metadata.json schema with access_control fields
4. ✅ Test full upload cycle locally

### Phase 4: Railway Deployment
1. ✅ Update Dockerfile/nixpacks.toml to include Node.js
2. ✅ Install `@lighthouse-web3/sdk` via npm in container
3. ✅ Deploy to Railway staging environment
4. ✅ Monitor logs for any errors
5. ✅ Test one upload cycle, verify CID in Lighthouse explorer

### Phase 5: Frontend Verification
1. ✅ Wait for new CID to be uploaded
2. ✅ Verify frontend can fetch metadata with new `access_control` fields
3. ✅ Test decryption with wallet connected (99 DADC balance)
4. ✅ Verify `lighthouse.fetchEncryptionKey()` succeeds
5. ✅ Confirm data decrypts and displays correctly

### Phase 6: Cleanup
1. ✅ Remove old custom AES encryption code (optional - keep as fallback)
2. ✅ Update documentation
3. ✅ Mark lighthouse_sdk_integration.py as deprecated

---

## 4. Testing Strategy

### 4.1 Unit Tests
```python
# tests/test_lighthouse_native_encryption.py

import pytest
from lighthouse_native_encryption import LighthouseNativeEncryption

def test_address_derivation():
    """Test wallet address derivation from private key."""
    lighthouse = LighthouseNativeEncryption(
        api_key="test_key",
        private_key="0x1234..."  # Test private key
    )
    assert lighthouse.wallet_address.startswith("0x")
    assert len(lighthouse.wallet_address) == 42

def test_auth_message_signing():
    """Test Lighthouse auth message signing."""
    lighthouse = LighthouseNativeEncryption(
        api_key="test_key",
        private_key="0x1234..."
    )
    signed = lighthouse._get_signed_message()
    assert signed.startswith("0x")
    assert len(signed) == 132  # 65 bytes * 2 + 0x prefix

@pytest.mark.integration
def test_upload_encrypted():
    """Test uploadEncrypted with real file."""
    lighthouse = LighthouseNativeEncryption(
        api_key="real_api_key",
        private_key="real_private_key"
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as f:
        f.write("Test content")
        f.flush()
        
        result = lighthouse.upload_encrypted(f.name, tag="test")
        
        assert "cid" in result
        assert result["cid"].startswith("Qm")

@pytest.mark.integration
def test_apply_access_control():
    """Test ERC20 access control application."""
    lighthouse = LighthouseNativeEncryption(
        api_key="real_api_key",
        private_key="real_private_key"
    )
    
    test_cid = "QmTestCID..."  # From previous upload
    
    result = lighthouse.apply_access_control(
        cid=test_cid,
        contract_address="0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
        chain="Sepolia",
        min_balance_wei=int(1e18)
    )
    
    assert result["status"] == "Success"
    assert result["cid"] == test_cid
```

### 4.2 Integration Testing
```bash
# Test locally before Railway deployment
cd apps/worker
python -m pytest tests/test_lighthouse_native_encryption.py -v

# Test full worker cycle
python run.py --test-upload
```

### 4.3 End-to-End Testing
1. Upload new file with native encryption
2. Check Lighthouse explorer: https://files.lighthouse.storage/viewFile/{CID}
3. Verify "Access Control" tab shows ERC20 condition
4. Test frontend decryption with wallet having 99 DADC
5. Test frontend rejection with wallet having 0 DADC

---

## 5. Rollback Plan

If anything breaks after deployment:

### Emergency Rollback
```python
# In run.py, keep old code as fallback

try:
    # Try native encryption
    result = lighthouse_native.encrypt_and_upload_with_gating(...)
except Exception as e:
    logger.error(f"Native encryption failed: {e}, falling back to custom AES")
    # Fallback to old custom AES
    result = lighthouse.encrypt_and_upload(...)
```

### Gradual Rollout
- Deploy with feature flag: `USE_LIGHTHOUSE_NATIVE_ENCRYPTION=false`
- Monitor for 24 hours
- Enable flag: `USE_LIGHTHOUSE_NATIVE_ENCRYPTION=true`
- If issues, disable flag immediately

---

## 6. Dependencies & Prerequisites

### Python Dependencies (add to requirements.txt)
```
eth-account>=0.10.0    # For signing messages
web3>=6.0.0            # For Ethereum interactions
```

### Node.js Dependencies (add to Railway container)
```json
{
  "dependencies": {
    "@lighthouse-web3/sdk": "^0.4.3",
    "ethers": "^6.0.0"
  }
}
```

### Environment Variables (Railway)
```bash
# Existing
LIGHTHOUSE_API_KEY=7e711ba4.5db09f1a785145159ab740254e63f070

# NEW - Add to Railway
LIGHTHOUSE_WALLET_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE  # For signing auth messages
DATACOIN_CONTRACT_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
DATACOIN_CHAIN=Sepolia
DATACOIN_MIN_BALANCE=1.0
```

### Dockerfile/nixpacks.toml Updates
```toml
# nixpacks.toml
[phases.setup]
nixPkgs = ["python39", "nodejs-18_x"]

[phases.install]
cmds = [
    "pip install -r requirements.txt",
    "npm install -g @lighthouse-web3/sdk ethers"
]
```

---

## 7. Success Criteria

### Technical Validation
- ✅ New CID uploaded with Lighthouse native encryption
- ✅ Access control visible in Lighthouse explorer
- ✅ Frontend `fetchEncryptionKey()` returns 200 OK (not 400)
- ✅ Data decrypts successfully in browser
- ✅ Token-gating enforced (tested with <1 DADC wallet)

### Operational Validation
- ✅ Worker upload cycle completes without errors
- ✅ Metadata.json updated with access_control fields
- ✅ Railway logs show no exceptions
- ✅ Cleanup job preserves new CID in protected list

### User Experience
- ✅ Frontend loads metadata (180 rows)
- ✅ Wallet connection works
- ✅ Token claim works (faucet functional)
- ✅ Decrypt button works with sufficient balance
- ✅ Clear error message if balance insufficient

---

## 8. Timeline Estimate

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| 1. Preparation | 2-3 hours | Create module, write tests |
| 2. Configuration | 30 min | Update settings, env vars |
| 3. Worker Integration | 1-2 hours | Modify run.py, test locally |
| 4. Railway Deployment | 1 hour | Update Dockerfile, deploy |
| 5. Frontend Verification | 30 min | Test decryption flow |
| 6. Cleanup & Docs | 1 hour | Update documentation |
| **TOTAL** | **6-8 hours** | Full implementation |

---

## 9. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Node.js subprocess fails | Medium | High | Fallback to old encryption |
| Lighthouse API rate limits | Low | Medium | Add retry logic with backoff |
| Private key exposure | Low | Critical | Store in Railway secrets, never log |
| CID access control conflict | Low | Medium | Check existing conditions before apply |
| Frontend still shows "cid not found" | Low | High | Verify chainType="evm", correct chain name |

---

## 10. Monitoring & Alerts

### Metrics to Track
1. Upload success rate (uploadEncrypted)
2. Access control application rate (applyAccessCondition)
3. Frontend decryption success rate (fetchEncryptionKey 200 vs 400)
4. Time to complete upload cycle
5. Node.js subprocess failures

### Logging
```python
logger.info(f"[Lighthouse Native] Uploading {file_path}...")
logger.info(f"[Lighthouse Native] CID: {cid}")
logger.info(f"[Lighthouse Native] Access control applied: {access_result}")
logger.error(f"[Lighthouse Native] Upload failed: {error}")
```

---

## 11. References

### Lighthouse SDK Documentation
- **uploadEncrypted()**: Found in `/src/Lighthouse/uploadEncrypted/encrypt/file/node.ts`
- **applyAccessCondition()**: Found in `/src/Lighthouse/encryption/applyAccessCondition.ts`
- **Test Examples**: Found in `/src/Lighthouse/tests/encryption.test.ts`

### Example Access Control Conditions (from tests)
```javascript
const conditions = [
  {
    id: 1,
    chain: "FantomTest",
    method: "balanceOf",
    standardContractType: "ERC20",
    contractAddress: "0xF0Bc72fA04aea04d04b1fA80B359Adb566E1c8B1",
    returnValueTest: { comparator: ">=", value: "0" },
    parameters: [":userAddress"]
  }
];
const aggregator = "([1])";
```

### Sepolia Adaptation
```javascript
const conditions = [
  {
    id: 1,
    chain: "Sepolia",  // ← Key: Chain name
    method: "balanceOf",
    standardContractType: "ERC20",
    contractAddress: "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",  // DataCoin
    returnValueTest: { 
      comparator: ">=", 
      value: "1000000000000000000"  // 1.0 DADC in wei
    },
    parameters: [":userAddress"]
  }
];
```

---

## 12. Next Steps

**Immediate Actions:**
1. ✅ Review this plan with user
2. ✅ Get approval to proceed
3. ✅ Create `lighthouse_native_encryption.py` module
4. ✅ Test Node.js subprocess locally
5. ✅ Update Railway environment variables

**Questions to Resolve:**
- ❓ Should we keep custom AES as permanent fallback or remove after validation?
- ❓ Do we have a test private key for Sepolia we can use?
- ❓ Should we add monitoring/alerting for decryption failures?

---

**Document Version:** 1.0  
**Created:** 2025-01-21  
**Author:** GitHub Copilot (AI Assistant)  
**Status:** READY FOR IMPLEMENTATION
