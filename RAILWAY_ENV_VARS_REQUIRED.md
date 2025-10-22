# 🚨 CRITICAL: Railway Environment Variables Required

## Missing Configuration Causing "Error encrypting file"

The Lighthouse native encryption is failing because **Railway needs these environment variables set manually**.

---

## ✅ Required Environment Variables

### 1. **LIGHTHOUSE_WALLET_PRIVATE_KEY** (CRITICAL - Currently Missing!)

```bash
Variable Name: LIGHTHOUSE_WALLET_PRIVATE_KEY
Description: Ethereum private key for signing Lighthouse authentication messages
Format: 0x followed by 64 hex characters
Example: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

**How to set in Railway:**
1. Go to your Railway project
2. Click on your service
3. Go to **Variables** tab
4. Click **New Variable**
5. Add:
   - Name: `LIGHTHOUSE_WALLET_PRIVATE_KEY`
   - Value: Your Ethereum private key (with 0x prefix)

**⚠️ SECURITY NOTES:**
- This should be a **dedicated wallet** for signing only (not your main wallet)
- The wallet doesn't need ETH or any funds
- It's used ONLY to sign authentication messages for Lighthouse
- Current wallet address in use: `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

---

### 2. **LIGHTHOUSE_API_KEY** (Should Already Be Set)

```bash
Variable Name: LIGHTHOUSE_API_KEY
Description: Lighthouse Storage API key for uploads
Format: API key from Lighthouse dashboard
Example: 7e711ba4.5db09f1a785145159ab740254e63f070
Status: ✅ Appears to be set (based on logs)
```

---

## 🔍 How to Verify Current Railway Variables

Run this in Railway's terminal or check Variables tab:

```bash
# List all environment variables (Railway dashboard)
echo $LIGHTHOUSE_API_KEY | wc -c          # Should be ~67 chars
echo $LIGHTHOUSE_WALLET_PRIVATE_KEY | wc -c  # Should be 66 chars (0x + 64 hex)
```

Expected output:
```
67  # LIGHTHOUSE_API_KEY length
66  # LIGHTHOUSE_WALLET_PRIVATE_KEY length (0x + 64 hex chars)
```

---

## 📋 Complete Railway Environment Variables Checklist

### Core Settings (Already Set):
- ✅ `BLOCKSCOUT_MCP_BASE` = https://eth.blockscout.com/api/v2
- ✅ `CHAIN_ID` = 1
- ✅ `DEX_POOL_A` = 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640
- ✅ `DEX_POOL_B` = 0x11b815efB8f581194ae79006d24E0d814B7697F6

### Lighthouse Settings:
- ✅ `LIGHTHOUSE_API_KEY` = <your-api-key> (appears set)
- ❌ `LIGHTHOUSE_WALLET_PRIVATE_KEY` = **MISSING - MUST SET**
- ✅ `LIGHTHOUSE_ENABLE_UPLOAD` = true (default)
- ✅ `LIGHTHOUSE_USE_NATIVE_ENCRYPTION` = true (default)

### DataCoin Token-Gating (Already Configured):
- ✅ `DATACOIN_CONTRACT_ADDRESS` = 0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
- ✅ `DATACOIN_CHAIN` = Sepolia
- ✅ `DATACOIN_MIN_BALANCE` = 1.0

---

## 🔧 How to Get a Private Key (If You Don't Have One)

### Option 1: Use Existing Wallet (MetaMask, etc.)

1. Open MetaMask
2. Click Account Details → Export Private Key
3. Enter password
4. Copy the private key (starts with 0x)

**⚠️ WARNING:** Only use a wallet you trust! This will be stored in Railway's environment.

### Option 2: Generate New Dedicated Wallet

```bash
# Using Node.js (run locally, not on Railway)
node -e "const ethers = require('ethers'); const wallet = ethers.Wallet.createRandom(); console.log('Address:', wallet.address); console.log('Private Key:', wallet.privateKey);"
```

Or use: https://vanity-eth.tk/ (be careful with security!)

---

## 🚀 After Setting the Variable

1. Set `LIGHTHOUSE_WALLET_PRIVATE_KEY` in Railway Variables
2. Railway will **automatically redeploy** (or click "Redeploy")
3. Watch logs for:
   ```
   [TIP #4] PARAMETER VALIDATION:
     ✓ publicKey (wallet): 0xYourWalletAddress
     ✓ publicKey has 0x: true
     ✓ publicKey length: 42 (should be 42)
     ✓ signedMessage format: 0x1234567890abcdef...
     ✓ signedMessage length: 132 (should be 132)
   ```

4. If successful, you'll see:
   ```
   [SUCCESS] textUploadEncrypted() completed in 2500ms ✓
   [VALIDATION] Checking response structure...
     ✓ CID: QmXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

---

## 🐛 Why This Was Failing

1. **Missing Private Key** → Can't sign authentication message
2. **Unsigned Message** → Lighthouse API rejects encryption request
3. **SDK Error** → Generic "Error encrypting file" at line 40 (saveShards)

The error at line 40 in the SDK is specifically the `saveShards()` function trying to authenticate with Lighthouse's Kavach encryption service. Without a signed message, it fails.

---

## 📚 Reference

- **Lighthouse Docs:** https://docs.lighthouse.storage/
- **Kavach (Encryption):** https://docs.lighthouse.storage/lighthouse-1/encryption
- **Token-Gating:** https://docs.lighthouse.storage/lighthouse-1/token-gating

---

## ✅ Quick Action

**Run this NOW in Railway Dashboard:**

1. Click your service
2. Go to **Variables** tab
3. Click **+ New Variable**
4. Add:
   ```
   Name: LIGHTHOUSE_WALLET_PRIVATE_KEY
   Value: 0x<your-64-char-hex-private-key>
   ```
5. Click **Add** → Service will auto-redeploy

That's it! The next deployment should show all the comprehensive debugging logs and (hopefully) succeed!
