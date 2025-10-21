# 🏆 1MB.io Setup for ETHOnline 2025 Prize

## 🚨 CRITICAL: Prize Requirement
**"Must Launch a data coin on https://1MB.io/"**

This guide shows you how to create your DEXArb DataCoin on 1MB.io for ETHOnline prize eligibility.

---

## 📋 Prize Requirements Checklist

### ✅ Already Complete:
- [x] Lighthouse storage ✅ (encrypted DEX data uploaded)
- [x] Lighthouse encryption ✅ (AES-256-GCM with access control)
- [x] Real-world dataset ✅ (mainnet DEX arbitrage via Alchemy)
- [x] Network deployment ✅ (Sepolia testnet)
- [x] Working demo ✅ (browser UI)
- [x] Open-source code ✅ (GitHub repo)

### ⏳ Next Steps:
- [ ] **Launch DataCoin on 1MB.io** ⚠️ REQUIRED FOR PRIZE
- [ ] Deploy frontend to Vercel
- [ ] Submit to ETHOnline

---

## 🎯 The Plan: 100% 1MB.io Platform

**We're using 1MB.io exclusively** - no custom contracts, no manual setup.

**Why?**
- ✅ Guaranteed prize compliance
- ✅ Automatic Uniswap pool creation  
- ✅ Built-in marketplace discovery
- ✅ Built-in faucet functionality (via Creator allocation)
- ✅ Takes 15 minutes total
- ✅ Judges can buy OR get free tokens

**What 1MB.io gives you:**
- Token contract deployed automatically
- Uniswap pool with initial liquidity
- Marketplace listing for discovery
- Trading interface
- Analytics dashboard

---

## 🚀 Creating Your DataCoin on 1MB.io

### Step 1: Prepare Assets

Before starting, gather:
- [ ] **Icon image** (512x512 PNG, transparent background)
- [ ] **Banner image** (1200x400 PNG, project hero)
- [ ] **Website link** (your Vercel app URL)
- [ ] **Social links** (GitHub, X/Twitter, Telegram)
- [ ] **Lock token** (LSDC - get from faucet)

**Get LSDC (Mock USDC):**
```solidity
// Visit LSDC faucet contract on Sepolia
// Call faucet() to get 10,000 LSDC
// Address: https://github.com/lighthouse-web3/data-dao-deployment
```

### Step 2: Connect to 1MB.io

1. Visit: https://1mb.io/create-coin
2. Click **"Connect Wallet"**
3. Connect MetaMask (Sepolia network)
4. Ensure wallet has:
   - ~0.05 SEP for gas
   - ≥100 LSDC for liquidity lock

### Step 3: Fill Token Information

```
Name: DEXArb Data Access Token
Symbol: DADC
Icon: [Upload 512x512 image]
Banner: [Upload 1200x400 image]
Website: https://your-app.vercel.app
Description: Token-gated access to real-time mainnet DEX arbitrage 
             opportunities. Data verified via zkTLS, encrypted with 
             Lighthouse, and auto-updated every 5 minutes.
```

### Step 4: Add Social Links

```
GitHub: https://github.com/shreyas-sovani/Alpha-Foundry
X (Twitter): [Your Twitter]
Telegram: [Your Telegram]
Farcaster: [Optional]
LinkedIn: [Optional]
```

### Step 5: Configure Tokenomics

**Recommended Settings for Hackathon:**

```
Chain: Sepolia ✅

Total Supply: 10,000 DADC

Allocations:
├─ Creator (You): 7,000 DADC (70%)
│  └─ Vesting: None (immediate access for faucet)
│
├─ Liquidity Pool: 2,000 DADC (20%)
│  └─ Auto-paired with LSDC on Uniswap
│
└─ Contributors: 1,000 DADC (10%)
   └─ Reserved for future rewards

Lock Token: LSDC (Lighthouse Mock USDC)
Lock Amount: 1,000 LSDC
├─ This pairs with 2,000 DADC in pool
└─ Initial price: 1 DADC = 0.5 LSDC

Minimum Lock: 100 LSDC (met)
```

**Why these numbers?**
- Creator allocation high → You can run faucet yourself
- Liquidity modest → Easy for judges to buy tokens
- Contributors small → Symbolic (optional future use)

### Step 6: Submit & Deploy

1. Click **"Submit Data Coin"**
2. **Transaction 1:** Approve LSDC spending
   - Confirm in MetaMask
   - Wait for confirmation (~15 sec)
3. **Transaction 2:** Create DataCoin
   - Confirms token deployment + Uniswap pool
   - Wait for confirmation (~30 sec)
4. **Success!** Your DataCoin is live on 1MB.io

### Step 7: Setup Free Token Distribution

Use your Creator allocation (7,000 DADC) for judge demos:

**Option 1: Manual Airdrops** (Simplest)
- Keep Creator tokens in your wallet
- Send 3-5 DADC to judges directly
- Track in spreadsheet

**Option 2: Simple Distribution Contract** (If needed)
- Deploy basic dispenser contract
- Transfer Creator tokens to it
- Judges call claim() for free tokens

**Recommendation:** Start with Option 1 (manual) for hackathon

### Step 8: Update Your Project

After creation, you'll have:
- New DADC token address (e.g., `0xNEW123...`)
- Uniswap pool address
- 1MB.io listing page

**Update these files:**

```bash
# .env
DATACOIN_CONTRACT_ADDRESS=0xNEW123...  # New token address

# apps/worker/out/unlock.html
const CONFIG = {
  DATACOIN_ADDRESS: '0xNEW123...',  # New token address
  ...
}

# scripts/quick_balance_check.py
CONTRACT_ADDRESS = "0xNEW123..."  # New token address
```

### Step 9: Test Integration

1. **Check 1MB.io listing:**
   - Visit: https://1mb.io/explore
   - Find your "DEXArb Data Access Token"
   - Verify details display correctly

2. **Test Uniswap pool:**
   - Visit Uniswap on Sepolia
   - Try to swap LSDC → DADC
   - Should work (don't actually buy, just check price)

3. **Test access control:**
   - Buy 1 DADC from Uniswap (or use faucet)
   - Visit unlock.html
   - Should show "✅ Eligible"

---

## 📱 Frontend Integration

### Update Unlock UI:

```javascript
// apps/worker/out/unlock.html

const CONFIG = {
  DATACOIN_ADDRESS: '0xYOUR_1MB_IO_TOKEN',  // From 1MB.io
  DATACOIN_MIN_BALANCE: 1.0,
  SEPOLIA_RPC: 'https://rpc.sepolia.org',
  METADATA_ENDPOINT: 'https://your-worker.railway.app/metadata',
  
  // New: Link to 1MB.io marketplace
  MARKETPLACE_URL: 'https://1mb.io/coin/YOUR_COIN_ID'
};

// Add "Buy Tokens" button
function renderBuyButton() {
  return `
    <a href="${CONFIG.MARKETPLACE_URL}" target="_blank">
      <button class="buy-btn">
        💰 Buy DADC on 1MB.io
      </button>
    </a>
  `;
}
```

### Add Marketplace Link:

```html
<!-- In unlock.html -->
<div class="marketplace-section">
  <h3>Don't have DADC tokens?</h3>
  <p>Buy on 1MB.io marketplace or use free faucet:</p>
  <div class="button-group">
    <a href="https://1mb.io/coin/YOUR_COIN_ID" target="_blank">
      <button>🛒 Buy on 1MB.io</button>
    </a>
    <a href="https://sepolia.etherscan.io/address/FAUCET_ADDRESS#writeContract" target="_blank">
      <button>💧 Free Faucet (3 DADC)</button>
    </a>
  </div>
</div>
```

---

## 🎬 Demo Flow (For Judges)

### Judge Experience:

1. **Discover DataCoin:**
   - Visit: https://1mb.io/explore
   - Find "DEXArb Data Access Token"
   - Read description, check volume/price

2. **Acquire Tokens (Two Options):**
   
   **Option A: Buy on 1MB.io**
   - Click "Trade" on coin page
   - Swap LSDC/WETH → DADC
   - Get 1+ DADC tokens
   
   **Option B: Free Faucet**
   - Visit faucet contract
   - Call `claim()` → Get 3 DADC free
   - Faster for hackathon demo

3. **Access Data:**
   - Visit: https://your-app.vercel.app/unlock
   - Connect MetaMask (Sepolia)
   - See access status: "✅ You have 3 DADC"
   - Click "Unlock Latest Data"
   - Download encrypted arbitrage opportunities

4. **View Results:**
   - JSONL file with DEX swap data
   - Columns: block, timestamp, token pairs, prices, profit margins
   - Real mainnet data, updated every 5 min

**Total Time:** ~3 minutes (including token acquisition)

---

## 📊 Prize Qualification Matrix

| Requirement | Status | Notes |
|-------------|--------|-------|
| Launch on 1MB.io | ✅ (after creation) | Must use platform |
| Lighthouse storage | ✅ Complete | Already uploading |
| Lighthouse encryption | ✅ Complete | AES-256-GCM working |
| Real-world dataset | ✅ Complete | Mainnet DEX data via Alchemy |
| Network deployment | ✅ Sepolia | Supported network |
| Working demo | ✅ Complete | unlock.html + CLI |
| Vercel deployment | ⏳ Pending | Need to deploy frontend |
| Open-source GitHub | ✅ Complete | Alpha-Foundry repo |

**Prize Eligibility:** 95% complete (just need 1MB.io + Vercel)

---

## ⚡ Quick Start (5-Minute Setup)

### For Creating New DataCoin:

```bash
# 1. Get LSDC tokens
Visit: [LSDC Faucet on Sepolia]
Call faucet() → Receive 10,000 LSDC

# 2. Create DataCoin
Visit: https://1mb.io/create-coin
Follow UI wizard (5 minutes)

# 3. Update config
# Update .env with new token address
DATACOIN_CONTRACT_ADDRESS=0xNEW...

# 4. Test
python3 scripts/quick_balance_check.py
# Enter wallet address → Check DADC balance
```

### For Using Existing Contract:

```bash
# 1. Deploy faucet
# Use Remix to deploy DADCFaucet.sol
# Constructor: 0xf376A613A6f6B193A898AF0b9B39a43dd9a41849

# 2. Mint tokens to faucet
# On your DADC contract:
mint(faucetAddress, 1000000000000000000000)  # 1000 DADC

# 3. Manually register on 1MB.io
# Contact Lighthouse team for existing contract integration

# 4. Test faucet
# Visit faucet on Etherscan
# Call claim() → Receive 3 DADC
```

---

## 🆘 Troubleshooting

### "Can't create DataCoin - insufficient LSDC"
**Solution:** Get LSDC from faucet first
- Visit faucet contract (link in Lighthouse docs)
- Call `faucet()` to receive 10,000 LSDC
- Then retry 1MB.io creation

### "Transaction failed during creation"
**Solution:** Check gas and approvals
- Ensure you have ~0.05 SEP for gas
- Approve LSDC spending before creating coin
- Try again with higher gas limit

### "Can't find my coin on marketplace"
**Solution:** Check creation status
- Visit: https://1mb.io/my-coins
- Verify coin was created successfully
- May take 1-2 minutes to appear in explore page

### "Uniswap pool not working"
**Solution:** Check liquidity allocation
- Pool needs ≥2% total supply for liquidity
- Lock amount must meet minimum (100 LSDC)
- Check pool address on coin details page

### "Want to use existing contract instead"
**Solution:** Contact Lighthouse
- DM @lighthouse_web3 on X/Twitter
- Explain you want to integrate existing ERC20
- They may manually add it to marketplace

---

## 📚 Additional Resources

### Official Documentation:
- **1MB.io Platform:** https://1mb.io/
- **DataCoin Creation Guide:** https://docs.lighthouse.storage/lighthouse-1/how-to/create-a-datacoin
- **Lighthouse Docs:** https://docs.lighthouse.storage/
- **GitHub Examples:** https://github.com/lighthouse-web3/data-dao-deployment

### ETHOnline 2025 Prize:
- **Prize Page:** [ETHOnline Lighthouse Prize Details]
- **Requirements:** Launch on 1MB.io + Lighthouse storage + real dataset
- **Deadline:** [Check ETHOnline schedule]
- **Prize Amount:** $500 (Best Consumer DataCoin)

### Support:
- **Lighthouse Discord:** [Link in docs]
- **X/Twitter:** @lighthouse_web3
- **Email:** mail@1mb.io

---

## ✅ Next Actions

### Immediate (Today):
1. [ ] Decide: Create new DataCoin OR integrate existing?
2. [ ] If new: Gather assets (icon, banner, links)
3. [ ] Get LSDC from faucet (need for liquidity)
4. [ ] Create DataCoin on 1MB.io (5 minutes)
5. [ ] Update config files with new address

### This Week:
6. [ ] Deploy faucet contract (for judge demos)
7. [ ] Test complete unlock flow
8. [ ] Deploy frontend to Vercel
9. [ ] Record demo video
10. [ ] Submit to ETHOnline

### Before Deadline:
11. [ ] Add 1MB.io marketplace link to UI
12. [ ] Update README with 1MB.io integration
13. [ ] Test judge experience end-to-end
14. [ ] Final submission to ETHOnline

---

## ✅ Final Checklist

Before creating your DataCoin:

- [ ] Have Sepolia ETH (~0.05 SEP for gas)
- [ ] Have LSDC tokens (get from faucet)
- [ ] Prepared icon image (512x512 PNG)
- [ ] Prepared banner image (1200x400 PNG)
- [ ] Website URL ready (will be your Vercel deployment)
- [ ] Social links ready (GitHub, X, Telegram)

After creating your DataCoin:

- [ ] Note new token address
- [ ] Update .env with DATACOIN_CONTRACT_ADDRESS
- [ ] Update unlock.html with new address
- [ ] Test token distribution (send to test wallet)
- [ ] Test unlock flow with eligible wallet
- [ ] Deploy frontend to Vercel
- [ ] Submit to ETHOnline

**Total Time:** 15-20 minutes from start to finish! 🚀

---

## 🆘 Need Help?

**Getting LSDC:**
- Check Lighthouse docs for faucet contract address
- Call `faucet()` function to get 10,000 LSDC
- Link: https://github.com/lighthouse-web3/data-dao-deployment

**1MB.io Creation Issues:**
- Ensure wallet connected to Sepolia
- Approve LSDC spending before creating coin
- Need ~0.05 SEP for gas (2 transactions)

**Testing Problems:**
- Send yourself 1-3 DADC from Creator allocation
- Update unlock.html with new token address
- Clear browser cache if MetaMask shows old data

**Lighthouse Support:**
- Discord: [Link in docs]
- X/Twitter: @lighthouse_web3
- Email: mail@1mb.io

---

**Ready to create your DataCoin?** Follow the steps above and you'll be prize-ready in 15 minutes!
