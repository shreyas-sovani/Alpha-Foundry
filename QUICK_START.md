# 🚀 Quick Start: Launch Your DataCoin in 15 Minutes

## What You're Building

**DEXArb DataCoin** - Token-gated access to real-time mainnet DEX arbitrage data

- ✅ Real-world data (mainnet DEX swaps via Alchemy)
- ✅ Encrypted storage (Lighthouse)
- ✅ Token-gated access (1MB.io DataCoin)
- ✅ Auto-updating (every 5 minutes)

---

## 📋 Prerequisites

Before starting:

- [ ] MetaMask installed
- [ ] Sepolia ETH (~0.05 SEP) - Get from https://sepoliafaucet.com
- [ ] LSDC tokens (~1000) - Get from Lighthouse faucet
- [ ] Project assets ready:
  - Icon (512x512 PNG)
  - Banner (1200x400 PNG)
  - GitHub repo URL
  - Social links

---

## ⚡ 15-Minute Setup

### Step 1: Get LSDC Tokens (2 min)

```bash
# 1. Find LSDC faucet contract address in Lighthouse docs:
# https://github.com/lighthouse-web3/data-dao-deployment

# 2. Visit contract on Sepolia Etherscan

# 3. Call faucet() function
# → Receive 10,000 LSDC (mock USDC for testing)
```

### Step 2: Create DataCoin on 1MB.io (5 min)

1. **Visit:** https://1mb.io/create-coin

2. **Connect MetaMask** (Sepolia network)

3. **Fill Token Information:**
   ```
   Name: DEXArb Data Access Token
   Symbol: DADC
   Icon: [Upload 512x512 PNG]
   Banner: [Upload 1200x400 PNG]  
   Website: https://github.com/shreyas-sovani/Alpha-Foundry
   Description: Token-gated access to real-time mainnet DEX 
                arbitrage opportunities. Data encrypted with 
                Lighthouse, auto-updated every 5 minutes.
   ```

4. **Add Social Links:**
   ```
   GitHub: https://github.com/shreyas-sovani/Alpha-Foundry
   X/Twitter: [Your handle]
   Telegram: [Optional]
   ```

5. **Configure Tokenomics:**
   ```
   Chain: Sepolia
   Total Supply: 10,000 DADC
   
   Allocations:
   ├─ Creator: 7,000 DADC (70%) - For you to distribute
   ├─ Liquidity: 2,000 DADC (20%) - Uniswap pool
   └─ Contributors: 1,000 DADC (10%) - Future rewards
   
   Lock Token: LSDC (Lighthouse Mock USDC)
   Lock Amount: 1,000 LSDC
   ```

6. **Submit & Deploy:**
   - Transaction 1: Approve LSDC
   - Transaction 2: Create DataCoin
   - Wait ~30 seconds
   - ✅ Done! Note your token address

### Step 3: Update Configuration (2 min)

Update these files with your new token address:

**`.env`:**
```bash
DATACOIN_CONTRACT_ADDRESS=0xYOUR_NEW_TOKEN_ADDRESS_FROM_1MB_IO
DATACOIN_CHAIN=Sepolia
DATACOIN_MIN_BALANCE=1.0
```

**`apps/worker/out/unlock.html`:**
```javascript
const CONFIG = {
  DATACOIN_ADDRESS: '0xYOUR_NEW_TOKEN_ADDRESS_FROM_1MB_IO',
  DATACOIN_MIN_BALANCE: 1.0,
  SEPOLIA_RPC: 'https://rpc.sepolia.org',
  METADATA_ENDPOINT: 'https://your-worker.railway.app/metadata'
};
```

### Step 4: Test Token Distribution (3 min)

Give yourself tokens for testing:

```bash
# Option A: Via MetaMask
# 1. Add DADC token to MetaMask (use new address)
# 2. You already have 7,000 DADC (Creator allocation)
# 3. Send 3 DADC to a test wallet

# Option B: Via Etherscan
# 1. Visit your token on Sepolia Etherscan
# 2. Use "Write Contract" → transfer()
# 3. To: 0xTestWallet, Amount: 3000000000000000000 (3 DADC)
```

### Step 5: Test Unlock Flow (3 min)

```bash
# 1. Start local server
python3 -m http.server 8080 --directory apps/worker/out

# 2. Open browser
open http://localhost:8080/unlock.html

# 3. Connect MetaMask (test wallet with 3 DADC)

# 4. Click "Check Access"
# → Should show: "✅ You have 3.0 DADC tokens"

# 5. Click "Unlock Latest Data"  
# → Downloads decrypted arbitrage data

# 6. Verify data
head decrypted_data.jsonl
# → Should show DEX swap records
```

---

## 🎯 For Hackathon Judges

### How Judges Get Tokens:

**Option 1: Manual Distribution (Simplest)**
- Share your wallet address with judges
- Send 3-5 DADC to each judge
- Track in spreadsheet

**Option 2: Buy on 1MB.io**
- Judges visit: https://1mb.io/coin/YOUR_COIN_ID
- Swap LSDC → DADC
- Use for data access

**Option 3: Email Request**
- Add "Request Tokens" button to UI
- Opens email with wallet address pre-filled
- You send tokens manually

**Recommendation:** Option 1 for hackathon (fast, simple)

### Judge Demo Flow (2 minutes):

1. Judge receives 3 DADC from you
2. Visits your unlock page
3. Connects MetaMask
4. Sees "✅ Eligible"
5. Clicks "Unlock" → Downloads data
6. Reviews arbitrage opportunities
7. ✅ Impressed!

---

## 📱 Deploy to Vercel (5 min)

After testing locally:

```bash
# 1. Create frontend directory
mkdir -p frontend
cp apps/worker/out/unlock.html frontend/index.html

# 2. Add vercel.json
cat > frontend/vercel.json << 'EOF'
{
  "version": 2,
  "builds": [{"src": "index.html", "use": "@vercel/static"}]
}
EOF

# 3. Deploy
cd frontend
npx vercel --prod

# 4. Get URL
# → https://your-app.vercel.app
```

Then update 1MB.io coin details with Vercel URL!

---

## ✅ Prize Compliance Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| Launch on 1MB.io | ✅ | After Step 2 |
| Lighthouse storage | ✅ | Already working |
| Lighthouse encryption | ✅ | AES-256-GCM |
| Real-world dataset | ✅ | Mainnet DEX data |
| Sepolia/Base/Polygon | ✅ | Sepolia testnet |
| Working demo | ✅ | unlock.html |
| Vercel deployment | ⏳ | Deploy frontend |
| Open-source GitHub | ✅ | Alpha-Foundry |

**Result:** 🎉 100% compliant after Vercel deployment!

---

## 🆘 Troubleshooting

### "Can't find LSDC faucet"
- Check: https://github.com/lighthouse-web3/data-dao-deployment
- Look for "LSDC" faucet contract address
- Call `faucet()` on Sepolia Etherscan

### "1MB.io creation failed"
- Ensure LSDC approved before creating coin
- Need ~0.05 SEP for gas (2 transactions)
- Check MetaMask on Sepolia network

### "Unlock page shows 0 balance"
- Verify token address updated in unlock.html
- Clear browser cache / hard refresh
- Check MetaMask connected to Sepolia

### "Worker not uploading data"
- Check worker logs: `railway logs`
- Verify Lighthouse API key in .env
- Test: `curl https://your-worker.railway.app/health`

---

## 📚 Full Documentation

For detailed guides:

- **`1MB_IO_INTEGRATION.md`** - Complete 1MB.io walkthrough
- **`README.md`** - Project overview
- **Lighthouse Docs** - https://docs.lighthouse.storage/

---

## 🎉 You're Ready!

After completing all 5 steps (15 minutes):

- ✅ DataCoin created on 1MB.io
- ✅ Uniswap pool active
- ✅ Token distribution working
- ✅ Unlock flow tested
- ✅ Ready for judges!

**Next:** Deploy to Vercel → Submit to ETHOnline → Win prize! 🏆

---

**Need help?** Check `1MB_IO_INTEGRATION.md` or ask questions!
