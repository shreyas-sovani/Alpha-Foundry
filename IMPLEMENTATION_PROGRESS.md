# Lighthouse Native Encryption - Implementation Progress

## ✅ Completed Steps

### Phase 1: Dependencies & Setup
- [x] Added `eth-account>=0.10.0` to requirements.txt
- [x] Installed eth-account Python package
- [x] Created package.json in apps/worker/
- [x] Installed @lighthouse-web3/sdk and ethers via npm
- [x] Verified Node.js v22.19.0 available
- [x] Verified SDK can be required from worker directory

### Phase 2: Configuration
- [x] Added new settings to settings.py:
  - `LIGHTHOUSE_WALLET_PRIVATE_KEY` (for signing)
  - `LIGHTHOUSE_USE_NATIVE_ENCRYPTION` (feature flag)
  - `DATACOIN_CONTRACT_ADDRESS`
  - `DATACOIN_CHAIN` 
  - `DATACOIN_MIN_BALANCE`
- [x] Updated print_redacted() to show new settings
- [x] Created lighthouse_native_encryption.py module

### Phase 3: Module Implementation
- [x] `LighthouseNativeEncryption` class created
- [x] `_get_signed_message()` - Auth message signing with eth-account
- [x] `upload_encrypted()` - Node.js subprocess for uploadEncrypted()
- [x] `apply_access_control()` - Node.js subprocess for applyAccessCondition()
- [x] `encrypt_and_upload_with_gating()` - Complete orchestration
- [x] Module syntax validated with py_compile

### Phase 4: Testing
- [x] Created test_lighthouse_native.py test suite
- [x] ✅ Test 1: Module Imports - PASS
- [x] ✅ Test 2: Wallet Derivation - PASS  
- [x] ✅ Test 3: Node.js Dependencies - PASS (verified manually)
- [x] ✅ Test 4: Auth Message Signing - PASS
- [x] Fixed signature format (0x prefix)
- [x] Fixed subprocess cwd to use worker directory

---

## 📋 Next Steps - Integration with run.py

### Step 1: Add Import to run.py
```python
from lighthouse_native_encryption import LighthouseNativeEncryption
```

### Step 2: Initialize in upload_to_lighthouse_and_cleanup()
```python
# Check if native encryption is enabled and configured
if (settings.LIGHTHOUSE_USE_NATIVE_ENCRYPTION and 
    settings.LIGHTHOUSE_WALLET_PRIVATE_KEY):
    
    lighthouse_native = LighthouseNativeEncryption(
        api_key=settings.LIGHTHOUSE_API_KEY,
        private_key=settings.LIGHTHOUSE_WALLET_PRIVATE_KEY
    )
```

### Step 3: Replace Upload Call
```python
# OLD (custom AES):
result = await loop.run_in_executor(
    None,
    lambda: lighthouse.encrypt_and_upload(...)
)

# NEW (native encryption):
result = await loop.run_in_executor(
    None,
    lambda: lighthouse_native.encrypt_and_upload_with_gating(
        file_path=str(jsonl_path),
        tag=f"dexarb_{settings.NETWORK_LABEL}",
        datacoin_address=settings.DATACOIN_CONTRACT_ADDRESS,
        chain=settings.DATACOIN_CHAIN,
        min_balance_dadc=settings.DATACOIN_MIN_BALANCE
    )
)
```

### Step 4: Update Metadata Schema
```python
metadata["encryption"] = result.get("encryption", "Lighthouse Native")
metadata["access_control"] = result.get("access_control", {})
```

### Step 5: Add Fallback Logic
```python
try:
    # Try native encryption
    result = lighthouse_native.encrypt_and_upload_with_gating(...)
except Exception as e:
    logger.error(f"Native encryption failed: {e}, falling back to custom AES")
    result = lighthouse.encrypt_and_upload(...)  # Old method
```

---

## 🔐 Environment Variables Needed

Add to Railway environment (and local .env for testing):

```bash
# Lighthouse Native Encryption
LIGHTHOUSE_WALLET_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
LIGHTHOUSE_USE_NATIVE_ENCRYPTION=true

# DataCoin Token-Gating (already correct defaults in settings.py)
DATACOIN_CONTRACT_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
DATACOIN_CHAIN=Sepolia
DATACOIN_MIN_BALANCE=1.0
```

⚠️ **IMPORTANT:** Do NOT commit the private key to git. Add to Railway secrets only.

---

## 📊 Current Status

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ✅ Module Implementation: COMPLETE                     │
│  ✅ Dependencies Installed: COMPLETE                    │
│  ✅ Configuration Added: COMPLETE                       │
│  ✅ Testing: 4/4 PASS                                   │
│  🔄 Integration with run.py: READY TO START            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Files Created/Modified:
1. ✅ `requirements.txt` - Added eth-account
2. ✅ `apps/worker/package.json` - Node.js dependencies
3. ✅ `apps/worker/lighthouse_native_encryption.py` - Main module
4. ✅ `apps/worker/test_lighthouse_native.py` - Test suite
5. ✅ `apps/worker/settings.py` - Added 5 new settings
6. 🔄 `apps/worker/run.py` - **NEXT: Integration needed**

---

## 🎯 ETA to Complete

- **Integration with run.py:** 30-45 minutes
- **Local testing:** 15-30 minutes  
- **Railway deployment:** 15-30 minutes
- **Frontend verification:** 15 minutes
- **Total:** ~2 hours

---

## ✅ Validation Criteria

Before considering this complete:

1. [ ] run.py successfully uploads with native encryption
2. [ ] Access control applied to CID
3. [ ] CID visible in Lighthouse explorer with "Access Control" tab
4. [ ] Metadata.json updated with access_control fields
5. [ ] Frontend fetchEncryptionKey() returns 200 (not 400)
6. [ ] Decryption works in browser with 99 DADC
7. [ ] Token-gating enforced (test with 0 DADC wallet)

---

**Status:** ✅ **READY FOR INTEGRATION**
**Next Action:** Integrate with run.py upload function
