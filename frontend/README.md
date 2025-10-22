# DEXArb Data Unlock - Frontend

Production-grade Next.js frontend for token-gated decentralized data access via Lighthouse Storage.

## 🎯 Features

- **Wallet Connection**: MetaMask integration with automatic network switching
- **Token Gating**: ERC20 balance verification (≥1 DADC required)
- **Self-Service Faucet**: Judges can claim 100 DADC tokens autonomously
- **Lighthouse SDK Integration**: Gasless signature + client-side decryption
- **Real-time Metadata**: Fetches latest CID from Railway backend API
- **Production-Ready**: TypeScript, Tailwind CSS, error handling, responsive design

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the UI.

### Environment Variables

Create `.env.local` with:

```env
# Backend API endpoint
NEXT_PUBLIC_METADATA_API=http://localhost:8787

# Sepolia Testnet Configuration
NEXT_PUBLIC_CHAIN_ID=11155111
NEXT_PUBLIC_CHAIN_NAME=Sepolia
NEXT_PUBLIC_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com

# Contract Addresses (Sepolia)
NEXT_PUBLIC_DATACOIN_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
NEXT_PUBLIC_FAUCET_ADDRESS=0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB

# Access Control
NEXT_PUBLIC_MIN_BALANCE=1.0
```

## 📦 Deploy to Vercel

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/shreyas-sovani/Alpha-Foundry/tree/main/frontend)

### Manual Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel

# Production deployment
vercel --prod
```

### Environment Variables on Vercel

In the Vercel dashboard, set these environment variables:

- `NEXT_PUBLIC_METADATA_API`: Your Railway backend URL (e.g., `https://af-hosted-production.up.railway.app`)
- `NEXT_PUBLIC_DATACOIN_ADDRESS`: `0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC`
- `NEXT_PUBLIC_FAUCET_ADDRESS`: `0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB`
- `NEXT_PUBLIC_CHAIN_ID`: `11155111`
- `NEXT_PUBLIC_CHAIN_NAME`: `Sepolia`
- `NEXT_PUBLIC_RPC_URL`: `https://ethereum-sepolia-rpc.publicnode.com`
- `NEXT_PUBLIC_MIN_BALANCE`: `1.0`

## 🔧 Technical Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Blockchain**: ethers.js v6
- **Data Fetching**: SWR
- **Decryption**: @lighthouse-web3/sdk v0.3.3

## 📝 User Flow

1. **Connect Wallet**: MetaMask connection with Sepolia network verification
2. **Check Balance**: Automatic DADC token balance check
3. **Claim Tokens** (if needed): Self-service faucet claim (100 DADC)
4. **View Metadata**: Real-time CID, update time, encryption stats from backend
5. **Unlock Data**: Gasless signature → Lighthouse access control → decrypt in-browser
6. **Download**: Save decrypted JSONL file locally

## 🔐 Security

- **Client-Side Decryption**: All decryption happens in the browser
- **Token Verification**: Lighthouse SDK checks ERC20 balance on-chain
- **No Private Keys**: User's keys never leave MetaMask
- **HTTPS Required**: Secure connection for wallet interactions

## 🐛 Troubleshooting

### Wrong Network
If MetaMask is on the wrong network, the UI will show a warning. Click the MetaMask extension and switch to Sepolia.

### Transaction Failed
Ensure you have Sepolia ETH for gas fees. Get free Sepolia ETH from:
- [Alchemy Faucet](https://sepoliafaucet.com/)
- [Infura Faucet](https://www.infura.io/faucet/sepolia)

### Can't Decrypt
Verify you have ≥1 DADC token. Check your balance on the UI or via Etherscan:
`https://sepolia.etherscan.io/token/0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC?a=YOUR_ADDRESS`

### No Data Available
The backend uploads new data every 5 minutes. If `latest_cid` is null, check back in a few minutes.

### CORS Issues (Local Development)
Make sure the backend HTTP server has CORS enabled. The worker's `http_server.py` should return:
```python
'Access-Control-Allow-Origin': '*'
```

## 📊 Contract Addresses (Sepolia)

- **DataCoin (DADC)**: `0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC`
- **Faucet**: `0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB`
- **Pool**: `0x8EF4B1670D382b47DBbF30ebE2Bb15e52Ed2236c`
- **Factory**: `0xC7Bc3432B0CcfeFb4237172340Cd8935f95f2990` (official 1MB.io)

## 🏆 ETHOnline 2025

Built for **ETHOnline 2025 - Lighthouse Prize**

**Track**: Decentralized Data Products  
**Features**:
- ✅ Encrypted data storage on Lighthouse (IPFS)
- ✅ ERC20 token-gated access control
- ✅ Gasless signature decryption workflow
- ✅ Production-grade UI/UX
- ✅ Self-service token distribution via faucet

## 📄 License

MIT License - See LICENSE file for details

---

**Links**:
- [Backend (Railway)](https://github.com/shreyas-sovani/Alpha-Foundry)
- [Lighthouse SDK Docs](https://docs.lighthouse.storage/)
- [1MB.io Factory](https://www.1mb.io/)
