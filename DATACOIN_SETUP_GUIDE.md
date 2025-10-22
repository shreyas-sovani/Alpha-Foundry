# DEXArb DataCoin Setup - Strategy 1

**Complete guide for creating DataCoin with 0% creator allocation for immediate token access**

## 🎯 Overview

**Your Wallet:** `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

**Strategy:** Create DataCoin with 0% creator allocation (no vesting) and 100% contributors allocation (immediate minting access).

## 📋 Prerequisites

### 1. Get LSDC Tokens (Sepolia)

You need **10,000 LSDC** minimum on Sepolia testnet.

**LSDC Contract:** `0x2EA104BCdF3A448409F2dc626e606FdCf969a5aE`

**How to get LSDC:**
- Join Lighthouse Discord: https://discord.gg/lighthouse
- Request testnet LSDC in #faucet channel
- Provide your address: `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

### 2. Upload Metadata to IPFS

Create a JSON file with your DataCoin metadata:

```json
{
  "name": "DEXArb Data Coin",
  "symbol": "DADC",
  "description": "DataCoin for DEXArb platform - ETHOnline 2025 Lighthouse Prize. Enables token-gated access to MEV trading data and analytics.",
  "image": "ipfs://YOUR_LOGO_CID",
  "external_url": "https://your-dexarb-demo.vercel.app",
  "attributes": [
    {
      "trait_type": "Category",
      "value": "MEV Trading Data"
    },
    {
      "trait_type": "Platform",
      "value": "DEXArb"
    },
    {
      "trait_type": "Hackathon",
      "value": "ETHOnline 2025"
    }
  ]
}
```

Upload to Lighthouse Storage and get the CID (e.g., `QmXXX...`).

### 3. Install Dependencies

```bash
cd /Users/shreyas/Desktop/af_hosted
npm install ethers@6 bcrypt dotenv
```

## 🔧 Configuration

### Step 1: Setup Environment Variables

Create `.env` file (or update existing):

```bash
# Your private key (KEEP SECRET!)
PRIVATE_KEY=your_private_key_without_0x_prefix

# Optional: Custom RPC
SEPOLIA_RPC_URL=https://1rpc.io/sepolia
```

### Step 2: Configure Creation Script

Edit `scripts/createDEXArbDataCoin.js`:

```javascript
// Update these values (lines 20-30)
const name = "DEXArb Data Coin";
const symbol = "DADC";
const description = "Your description...";
const image = "ipfs://YOUR_LOGO_CID"; // From metadata upload
const email = "your-email@example.com";
const telegram = "your_telegram_handle";
const tokenURI = "ipfs://YOUR_METADATA_CID"; // From metadata upload
const creatorAddress = "0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3"; // Your address
```

**Important:** Keep these allocation settings (Strategy 1):
```javascript
const creatorAllocationBps = 0;      // 0% - No vesting
const contributorsAllocationBps = 10000; // 100% - Immediate access
const liquidityAllocationBps = 0;    // 0% - No Uniswap pool
const creatorVesting = 0;            // Not used
```

## 🚀 Deployment

### Create the DataCoin

```bash
node scripts/createDEXArbDataCoin.js
```

**Expected Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 DATACOIN SUCCESSFULLY CREATED!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Deployment Details:

   🪙  DataCoin Address: 0xYourDataCoinAddress...
   💧  Pool Address: 0x0000000000000000000000000000000000000000
   👤  Creator: 0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3
   ...
```

**Save the DataCoin Address!** You'll need it for minting and frontend integration.

## 💰 Minting Tokens

After DataCoin creation, mint tokens for judges or your distribution system.

### Option 1: Mint to Multiple Addresses

Edit `scripts/mintTokens.js`:

```javascript
// Update DataCoin address (line 17)
const DATACOIN_ADDRESS = "0xYourDataCoinAddress"; // From creation output

// Update judge addresses (lines 24-29)
const MINT_TO_JUDGES = [
  { address: "0xJudge1Address", amount: "100" },
  { address: "0xJudge2Address", amount: "100" },
  { address: "0xJudge3Address", amount: "100" },
];
```

Run minting:

```bash
node scripts/mintTokens.js
```

### Option 2: Mint to Distribution Contract

If you have a distribution contract:

```javascript
const MINT_TO_DISTRIBUTION_CONTRACT = {
  enabled: true,
  address: "0xYourDistributionContractAddress",
  amount: "10000", // 10,000 DADC
};
```

## 🔗 Frontend Integration

Update your `unlock.html` or main frontend file:

```javascript
// Contract addresses
const DATACOIN_ADDRESS = "0xYourDataCoinAddress"; // From creation
const REQUIRED_BALANCE = 3; // 3 DADC required to access features

// DataCoin ABI (minimal)
const DATACOIN_ABI = [
  "function balanceOf(address) external view returns (uint256)",
  "function name() external view returns (string)",
  "function symbol() external view returns (string)"
];

// Check if user has tokens
async function checkAccess() {
  const provider = new ethers.BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const datacoin = new ethers.Contract(DATACOIN_ADDRESS, DATACOIN_ABI, provider);
  
  const balance = await datacoin.balanceOf(signer.address);
  const hasAccess = ethers.formatUnits(balance, 18) >= REQUIRED_BALANCE;
  
  return hasAccess;
}
```

## 🧪 Testing Checklist

- [ ] DataCoin created successfully
- [ ] Verified on Sepolia Etherscan
- [ ] Tokens minted to test addresses
- [ ] Frontend shows token balance
- [ ] Access control works (balance >= 3 DADC)
- [ ] Submission README includes DataCoin address

## 📝 For ETHOnline Submission

Include in your submission:

### README.md Section

```markdown
## 🏆 Lighthouse Prize - 1MB.io Integration

**DataCoin Address (Sepolia):** 0xYourDataCoinAddress

**Created via 1MB.io Platform:**
- Official DataCoinFactory: `0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990`
- Lock Asset: 10,000 LSDC
- Creation Transaction: https://sepolia.etherscan.io/tx/YOUR_TX_HASH

**For Judges:**
Tokens have been distributed to judge addresses via minting.
Connect wallet to access DEXArb platform features.
```

### Video Demo Script (2 minutes)

1. **Show DataCoin on Etherscan** (30s)
   - "Created via 1MB.io official factory"
   - Show 10,000 LSDC locked
   - Show 0% creator, 100% contributors allocation

2. **Show Token Balance** (30s)
   - Connect MetaMask
   - Show DADC balance
   - Explain 3 DADC requirement

3. **Demo Gated Feature** (45s)
   - Try accessing without tokens (blocked)
   - Connect wallet with tokens (access granted)
   - Show DEXArb data/analytics

4. **Explain Benefits** (15s)
   - "Token-gated MEV data access"
   - "Built on Lighthouse platform"
   - "Immediate distribution for async judging"

## 🐛 Troubleshooting

### "Insufficient LSDC balance"

Get more LSDC from Lighthouse Discord faucet.

### "InvalidVestingDuration" Error

If 0 vesting fails, update the script:

```javascript
const creatorAllocationBps = 1000;  // 10%
const contributorsAllocationBps = 9000; // 90%
const creatorVesting = 1; // 1 second
```

Then immediately after creation, claim vesting:

```javascript
// Using ethers.js
const datacoin = new ethers.Contract(dataCoinAddress, DatacoinABI, wallet);
await datacoin.claimVesting();
```

### "Only creator can mint"

Ensure you're using the same wallet that created the DataCoin. The creator address must match `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`.

### Transaction Reverted

Check:
1. Enough ETH for gas (~0.01 ETH)
2. Connected to Sepolia network
3. LSDC approval succeeded
4. Using correct factory address

## 📚 Additional Resources

**Official Repos:**
- data-dao-deployment: https://github.com/lighthouse-web3/data-dao-deployment
- 1MB.io Platform: https://1mb.io

**Your Scripts:**
- `scripts/createDEXArbDataCoin.js` - DataCoin creation
- `scripts/mintTokens.js` - Token minting
- `scripts/abi/` - Contract ABIs

**Support:**
- Lighthouse Discord: https://discord.gg/lighthouse
- ETHOnline Discord: Check #lighthouse channel

## ✅ Success Criteria

After completing this guide:

✅ DataCoin created on 1MB.io platform (via official factory)
✅ 10,000 LSDC locked
✅ Tokens minted to judge addresses
✅ Frontend integrated with token gating
✅ Test access successful
✅ Ready for ETHOnline submission

**Congratulations!** Your DEXArb DataCoin is ready for async hackathon judging. 🎉

---

## 🔍 Quick Reference

**Your Address:** `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

**Key Addresses (Sepolia):**
- DataCoinFactory: `0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990`
- LSDC Token: `0x2EA104BCdF3A448409F2dc626e606FdCf969a5aE`
- Your DataCoin: `0x...` (from creation script output)

**Commands:**
```bash
# Create DataCoin
node scripts/createDEXArbDataCoin.js

# Mint tokens
node scripts/mintTokens.js
```

**Verification:**
```
https://sepolia.etherscan.io/address/YOUR_DATACOIN_ADDRESS
```
