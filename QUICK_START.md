# 🚀 Quick Start - DEXArb DataCoin (10 minutes)

**Your Wallet:** `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

## ⚡ Steps

### 1. Install Dependencies (2 min)

```bash
npm install
```

### 2. Get LSDC Tokens (External)

- Join: https://discord.gg/lighthouse
- Request 10,000 LSDC for `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

### 3. Upload Metadata (3 min)

Upload to Lighthouse Storage:
```json
{
  "name": "DEXArb Data Coin",
  "symbol": "DADC",
  "description": "Token-gated MEV data access",
  "image": "ipfs://YOUR_LOGO_CID"
}
```

Get CID: `ipfs://QmXXX...`

### 4. Configure Script (2 min)

Edit `scripts/createDEXArbDataCoin.js` (lines 25-30):

```javascript
const image = "ipfs://YOUR_LOGO_CID";
const email = "your@email.com";
const telegram = "your_handle";
const tokenURI = "ipfs://YOUR_METADATA_CID";
```

Setup `.env`:
```bash
PRIVATE_KEY=your_private_key_here
```

### 5. Create DataCoin (3 min)

```bash
npm run create
```

**Save the output DataCoin address!**

### 6. Mint Tokens (Optional)

Edit `scripts/mintTokens.js`:
```javascript
const DATACOIN_ADDRESS = "0xYourOutputAddress";
```

Run:
```bash
npm run mint
```

## ✅ Done!

Your DataCoin is ready. See `DATACOIN_SETUP_GUIDE.md` for details.

**Next:** Update frontend with DataCoin address and test token gating.

---

## Old Platform Setup (Deprecated)

The following was the old Alpha Foundry worker platform setup:

## Step 1: Clone and Setup (2 minutes)
