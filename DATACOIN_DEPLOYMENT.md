# DEXArb DataCoin Deployment

**Created:** October 22, 2025  
**Network:** Sepolia Testnet  
**Purpose:** ETHOnline 2025 - Lighthouse Prize Track

## 🪙 Contract Addresses

| Contract | Address | Explorer |
|----------|---------|----------|
| **DataCoin** | `0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC` | [View on Etherscan](https://sepolia.etherscan.io/address/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC) |
| **Liquidity Pool** | `0x8EF4B1670D382b47DBbF30ebE2Bb15e52Ed2236c` | [View on Etherscan](https://sepolia.etherscan.io/address/0x8EF4B1670D382b47DBbF30ebE2Bb15e52Ed2236c) |
| **Factory** | `0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990` | [View on Etherscan](https://sepolia.etherscan.io/address/0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990) |
| **Lock Token (LSDC)** | `0x2EA104BCdF3A448409F2dc626e606FdCf969a5aE` | [View on Etherscan](https://sepolia.etherscan.io/address/0x2EA104BCdF3A448409F2dc626e606FdCf969a5aE) |

## 📋 Token Details

- **Name:** DEXArb Data Coin
- **Symbol:** DADC
- **Total Supply:** 100,000,000,000 DADC (100 billion)
- **Decimals:** 18
- **Metadata:** ipfs://bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy
- **Logo:** ipfs://bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4

## 🎯 Allocation Strategy

**Strategy 1 (Modified for Factory Fees):**
- **Creator Allocation:** 0% (no vesting required)
- **Contributors Allocation:** 99% (98,990,000,000 DADC available for minting)
- **Liquidity Allocation:** 1% (1,000,000,000 DADC in Uniswap pool)

### Why This Configuration?
- **No Vesting Delays:** 0% creator allocation means no 1-month minimum vesting
- **Maximum Minting Capacity:** 99% of supply available for immediate distribution
- **Factory Compliance:** 1% liquidity satisfies factory fee requirements
- **Async Hackathon Ready:** Creator can mint tokens to judges anytime

## 🔒 Lock Configuration

- **Lock Asset:** LSDC (Lighthouse Sepolia Data Coin)
- **Amount Locked:** 10,000 LSDC
- **Lock Duration:** Permanent (as per 1MB.io platform design)

## 📦 Deployment Transaction

- **Transaction Hash:** `0x0bf7c4da8b9b05137d08af046d8d360863398f91d747b2d4ac3f5c4bafe235ac`
- **Block Number:** 9,464,321
- **Gas Used:** 3,727,223
- **Deployed By:** `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`
- **Timestamp:** 2025-10-22 07:18:17 UTC

[View Transaction on Etherscan](https://sepolia.etherscan.io/tx/0x0bf7c4da8b9b05137d08af046d8d360863398f91d747b2d4ac3f5c4bafe235ac)

## 👤 Access Control

**Creator Address:** `0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3`

**Roles Granted:**
- `DEFAULT_ADMIN_ROLE`: Full administrative control
- `MINTER_ROLE`: Can mint tokens to any address (up to contributors allocation)

## 🎪 For ETHOnline 2025 Judges

### How Judges Get Access

1. **Creator Mints Tokens:** Project creator runs `node scripts/mintTokens.js`
2. **Judges Receive DADC:** Tokens sent directly to judge wallet addresses
3. **Token-Gated Access:** Frontend checks DADC balance before showing data
4. **No Manual Claims:** Unlike faucets, judges don't need to claim anything

### Token Distribution

You can mint up to **98,990,000,000 DADC** to judges and reviewers.

Example distribution:
- **5 ETHOnline Judges:** 100 DADC each = 500 DADC total
- **Community Reviewers:** 50 DADC each
- **Project Demonstrators:** 200 DADC each

## 🔧 Minting Tokens

### Update Judge Addresses

Edit `scripts/mintTokens.js`:

```javascript
const MINT_TO_JUDGES = [
  { address: "0xJudge1Address", amount: "100" },
  { address: "0xJudge2Address", amount: "100" },
  { address: "0xJudge3Address", amount: "100" },
  // Add more judges as needed
];
```

### Run Minting Script

```bash
node scripts/mintTokens.js
```

This will:
1. Connect to Sepolia
2. Verify you have MINTER_ROLE (you do, as creator)
3. Check contributors allocation capacity (99% = 98.99B DADC)
4. Mint tokens to each judge address
5. Display transaction hashes

## 🌐 Frontend Integration

### Update Your unlock.html

```javascript
// Token-gating configuration
const DATACOIN_ADDRESS = "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC";
const DATACOIN_CHAIN = "Sepolia"; // Or chain ID: 11155111
const DATACOIN_MIN_BALANCE = 1.0; // Minimum 1 DADC token

// Check user's DADC balance before showing data
async function checkDataCoinBalance(userAddress) {
  const datacoin = new ethers.Contract(
    DATACOIN_ADDRESS,
    ["function balanceOf(address) view returns (uint256)"],
    provider
  );
  
  const balance = await datacoin.balanceOf(userAddress);
  const balanceFormatted = ethers.formatUnits(balance, 18);
  
  return parseFloat(balanceFormatted) >= DATACOIN_MIN_BALANCE;
}
```

## 📝 Submission Checklist

For ETHOnline 2025 Lighthouse Prize:

- [x] Created DataCoin on 1MB.io platform (via official factory)
- [x] Used official factory: `0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990`
- [x] Locked required LSDC (10,000 tokens)
- [x] Metadata uploaded to IPFS via Lighthouse
- [ ] Mint tokens to judge addresses
- [ ] Update frontend with DataCoin address
- [ ] Test token-gating with judge wallets
- [ ] Add DataCoin info to README
- [ ] Submit project with DataCoin address

## 🔗 Important Links

- **1MB.io Platform:** https://1mb.io/
- **DataCoin on Etherscan:** https://sepolia.etherscan.io/address/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
- **Factory Contract:** https://sepolia.etherscan.io/address/0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990
- **Lighthouse Storage:** https://files.lighthouse.storage
- **Metadata JSON:** ipfs://bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy
- **Logo Image:** ipfs://bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4

## 🎯 Prize Requirements Met

✅ **"Must Launch on 1MB.io"** - Deployed via official factory  
✅ **Lock Asset** - 10,000 LSDC locked  
✅ **Token Metadata** - Uploaded to IPFS via Lighthouse  
✅ **Token-Gated Access** - DADC balance check in frontend  
✅ **Async Judging Ready** - No vesting delays

## 📊 Deployment JSON

```json
{
  "network": "sepolia",
  "timestamp": "2025-10-22T07:18:17.656Z",
  "dataCoinAddress": "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
  "poolAddress": "0x8EF4B1670D382b47DBbF30ebE2Bb15e52Ed2236c",
  "creator": "0xD2aA21AF4faa840Dea890DB2C6649AACF2C80Ff3",
  "lockAsset": "LSDC",
  "lockAmount": 10000,
  "transactionHash": "0x0bf7c4da8b9b05137d08af046d8d360863398f91d747b2d4ac3f5c4bafe235ac",
  "blockNumber": 9464321,
  "gasUsed": 3727223,
  "allocation": {
    "creator": "0%",
    "contributors": "99%",
    "liquidity": "1%"
  },
  "vesting": "None (0% creator allocation)",
  "totalSupply": "100000000000000000000000000000",
  "mintingCapacity": "98990000000000000000000000000",
  "metadata": {
    "tokenURI": "ipfs://bafkreie73wguaf7yucgzcudbkivtgtxzvyv2efjg24s76j67lu7cbt7vcy",
    "image": "ipfs://bafybeih5j5recyxiwscbtjl7o5rmv22rijmeq552iovrguas45s4766yw4"
  }
}
```

---

**Status:** ✅ Deployed and Ready for Judging  
**Next Step:** Run `node scripts/mintTokens.js` to distribute tokens to judges
