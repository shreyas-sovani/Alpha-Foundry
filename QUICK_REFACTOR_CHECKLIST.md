# Lighthouse Native Encryption - Quick Refactor Checklist

## 🎯 Goal
Replace custom AES encryption with Lighthouse native encryption + ERC20 token-gating so frontend decryption works.

## 📋 Quick Steps

### 1. Create New Module ✅
**File:** `apps/worker/lighthouse_native_encryption.py`
- Implement `LighthouseNativeEncryption` class
- Use Node.js subprocess for `uploadEncrypted()` and `applyAccessCondition()`
- Handle auth message signing with `eth-account`

### 2. Install Dependencies ✅
```bash
# Python
pip install eth-account web3

# Node.js (on Railway)
npm install -g @lighthouse-web3/sdk ethers
```

### 3. Add Environment Variables (Railway) ✅
```bash
LIGHTHOUSE_WALLET_PRIVATE_KEY=0xYOUR_KEY_HERE
DATACOIN_CONTRACT_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
DATACOIN_CHAIN=Sepolia
DATACOIN_MIN_BALANCE=1.0
```

### 4. Update Worker ✅
**File:** `apps/worker/run.py`

Replace:
```python
result = lighthouse.encrypt_and_upload(...)
```

With:
```python
lighthouse_native = LighthouseNativeEncryption(...)
result = lighthouse_native.encrypt_and_upload_with_gating(
    file_path=jsonl_path,
    datacoin_address=settings.DATACOIN_CONTRACT_ADDRESS,
    chain="Sepolia",
    min_balance_dadc=1.0
)
```

### 5. Update Metadata Schema ✅
Add to `metadata.json`:
```json
{
  "encryption": "Lighthouse Native",
  "access_control": {
    "contract": "0x8d302...",
    "chain": "Sepolia",
    "min_balance": "1.0 DADC"
  }
}
```

### 6. Test Locally ✅
```bash
python -m pytest tests/test_lighthouse_native_encryption.py
python run.py --test-upload
```

### 7. Deploy to Railway ✅
```bash
git add .
git commit -m "feat: add Lighthouse native encryption with ERC20 gating"
git push origin main
```

### 8. Verify Frontend Works ✅
1. Wait for new upload
2. Check frontend fetches new CID
3. Test decryption with wallet (99 DADC)
4. Confirm `lighthouse.fetchEncryptionKey()` returns 200 OK

## ⚡ Critical Condition Structure

```javascript
const conditions = [{
  id: 1,
  chain: "Sepolia",  // ← MUST match Lighthouse chain names
  method: "balanceOf",
  standardContractType: "ERC20",
  contractAddress: "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
  returnValueTest: { 
    comparator: ">=", 
    value: "1000000000000000000"  // 1 DADC in wei
  },
  parameters: [":userAddress"]
}];
const aggregator = "([1])";
```

## 🔍 Verification Checklist

- [ ] Node.js and `@lighthouse-web3/sdk` installed on Railway
- [ ] Private key added to Railway secrets (not committed to git)
- [ ] Upload completes without errors
- [ ] CID appears in Lighthouse explorer with "Access Control" tab
- [ ] Frontend `fetchEncryptionKey()` succeeds (not 400 error)
- [ ] Data decrypts in browser
- [ ] Token-gating enforced (test with 0 DADC wallet)

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| "cid not found" error | Access control not applied - check `applyAccessCondition` call |
| Node.js subprocess fails | Ensure Node.js 18+ and SDK installed |
| "Invalid chain" error | Use "Sepolia" not "sepolia" or "11155111" |
| Private key errors | Use `eth-account` to sign, not raw signatures |

## 📚 Key Files

- **Implementation Plan:** `LIGHTHOUSE_NATIVE_ENCRYPTION_REFACTOR_PLAN.md` (detailed)
- **Module Code:** `apps/worker/lighthouse_native_encryption.py` (create)
- **Worker Integration:** `apps/worker/run.py` (modify)
- **Settings:** `apps/worker/settings.py` (add vars)
- **Tests:** `tests/test_lighthouse_native_encryption.py` (create)

## ⏱️ Estimated Time: 6-8 hours

---
**Quick Start:** Read full plan in `LIGHTHOUSE_NATIVE_ENCRYPTION_REFACTOR_PLAN.md`
