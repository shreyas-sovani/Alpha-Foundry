# 🎨 Frontend Architecture - DEXArb Data Unlock

**Framework:** Next.js 14 with React 18  
**Styling:** Tailwind CSS  
**Blockchain:** ethers.js v6  
**Encryption:** Lighthouse SDK v0.3.3  
**State:** React Hooks + SWR for data fetching  

---

## 📁 Project Structure

```
frontend/
├── app/
│   ├── globals.css           # Global styles + Tailwind
│   ├── layout.tsx             # Root layout
│   └── page.tsx               # Main unlock page (767 lines)
├── types/
│   └── window.d.ts            # TypeScript window extensions
├── public/                    # Static assets
├── package.json               # Dependencies
├── next.config.js             # Next.js configuration
├── tailwind.config.js         # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
├── .env.local                 # Local development (localhost:8787)
└── .env.production            # Production (Railway URL)
```

---

## 🏗️ Architecture Overview

### Component Hierarchy

```
UnlockPage (page.tsx)
├── Header Section
├── Status Card
│   ├── Metadata Display
│   ├── Encryption Status
│   └── Auto-refresh (10s)
├── Wallet Connection Section
│   ├── Connect Button
│   ├── Wallet Info Display
│   └── Network Status
├── Token Claiming Section
│   ├── Claim Button
│   ├── Balance Display
│   └── Eligibility Check
├── Data Unlocking Section
│   ├── Unlock Button
│   ├── Decryption Flow
│   └── Progress Messages
├── Decrypted Data Display
│   ├── Data Preview
│   ├── Download Button
│   └── Stats Display
└── FAQ Section
```

---

## 🔄 Data Flow

### 1. Metadata Fetching (SWR)
```typescript
const { data: metadata, error: metadataError } = useSWR<Metadata>(
  `${METADATA_API}/metadata`,
  fetcher,
  { refreshInterval: 10000 }  // Auto-refresh every 10s
)
```

**API Response:**
```json
{
  "schema_version": "1.1",
  "latest_cid": "QmPm7ohpL1UxextmTFhmTUXVC7hL3zgBnuAnzYr2ShpSjd",
  "last_updated": "2025-10-22T16:48:35Z",
  "rows": 110,
  "freshness_minutes": 0,
  "encryption": {
    "enabled": true,
    "algorithm": "lighthouse-native",
    "status": "active"
  }
}
```

### 2. Wallet Connection Flow
```
User clicks "Connect Wallet"
    ↓
Check if MetaMask installed
    ↓
Request accounts (eth_requestAccounts)
    ↓
Get chain ID
    ↓
Create provider & signer
    ↓
Fetch DADC token balance
    ↓
Check if claimed tokens
    ↓
Update wallet state
```

### 3. Token Claiming Flow
```
User clicks "Claim Tokens"
    ↓
Check network (must be Sepolia)
    ↓
Check if already claimed
    ↓
Call faucet.claimTokens()
    ↓
Wait for transaction
    ↓
Refresh balance
    ↓
Enable unlock button
```

### 4. Data Decryption Flow (The Complex Part!)
```
User clicks "Unlock Data"
    ↓
Step 1: Get auth message from Lighthouse
    lighthouse.getAuthMessage(address)
    ↓
Step 2: Sign message with MetaMask
    signer.signMessage(messageText)
    ↓
Step 3: Fetch decryption key (access control check)
    lighthouse.fetchEncryptionKey(cid, address, signature)
    [Lighthouse verifies: balance >= 1.0 DADC]
    ↓
Step 4: Download & decrypt file
    lighthouse.decryptFile(cid, key)
    ↓
Step 5: Convert to string (CRITICAL FIX)
    Handle Blob/ArrayBuffer/String types
    ↓
Display decrypted data
```

---

## 🐛 Critical Bug Fix - Decryption Data Type

### The Problem

**Error:** `TypeError: decrypted.substring is not a function`

**Location:** Line 359 in original code

**Cause:** `lighthouse.decryptFile()` returns different data types:
- Sometimes a `Blob`
- Sometimes an `ArrayBuffer`
- Sometimes a plain `string`
- Sometimes `{data: Blob}`

The code assumed it would always be a string.

### The Solution

Added comprehensive type handling:

```typescript
const decrypted = await lighthouse.decryptFile(cid, key)

console.log('Decrypted type:', typeof decrypted, decrypted?.constructor?.name)

// Convert to string based on type
let decryptedText: string

if (typeof decrypted === 'string') {
  // Already a string
  decryptedText = decrypted
  
} else if (decrypted instanceof Blob) {
  // Blob → read as text
  decryptedText = await decrypted.text()
  
} else if (decrypted instanceof ArrayBuffer) {
  // ArrayBuffer → decode to string
  decryptedText = new TextDecoder().decode(decrypted)
  
} else if (decrypted?.data) {
  // Wrapped in object with .data property
  const data = decrypted.data
  if (typeof data === 'string') {
    decryptedText = data
  } else if (data instanceof Blob) {
    decryptedText = await data.text()
  } else {
    decryptedText = JSON.stringify(data, null, 2)
  }
  
} else {
  // Fallback: convert to string
  decryptedText = String(decrypted)
}

setDecryptedData(decryptedText)
```

**Lines Changed:** 353-389 in `page.tsx`

---

## 🔐 Token-Gating Implementation

### Access Control Check

The magic happens in Lighthouse's `fetchEncryptionKey()`:

```typescript
const keyObject = await lighthouse.fetchEncryptionKey(
  cid,        // Encrypted file CID
  address,    // User's wallet address
  signature   // Signed message proving ownership
)
```

**Behind the scenes:**
1. Lighthouse kavach nodes receive the request
2. They call the ERC20 contract: `balanceOf(address)`
3. Check: `balance >= 1000000000000000000` (1.0 DADC in wei)
4. If true: Return decryption key
5. If false: Reject with "access denied"

### Contract Configuration

```typescript
{
  "id": 1,
  "chain": "Sepolia",
  "method": "balanceOf",
  "standardContractType": "ERC20",
  "contractAddress": "0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC",
  "returnValueTest": {
    "comparator": ">=",
    "value": "1000000000000000000"  // 1.0 DADC
  },
  "parameters": [":userAddress"]
}
```

This configuration is applied by the backend when uploading encrypted data.

---

## 🎯 Environment Configuration

### Development (.env.local)
```bash
NEXT_PUBLIC_METADATA_API=http://localhost:8787
NEXT_PUBLIC_CHAIN_ID=11155111
NEXT_PUBLIC_CHAIN_NAME=Sepolia
NEXT_PUBLIC_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
NEXT_PUBLIC_DATACOIN_ADDRESS=0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC
NEXT_PUBLIC_FAUCET_ADDRESS=0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB
NEXT_PUBLIC_MIN_BALANCE=1.0
```

### Production (.env.production)
```bash
NEXT_PUBLIC_METADATA_API=https://web-production-279f4.up.railway.app
# ... same for other vars
```

**Key Difference:** Production uses Railway backend URL instead of localhost.

---

## 📡 API Integration

### Backend Endpoints Used

#### 1. GET /metadata
**Purpose:** Get latest encrypted file info  
**Refresh:** Every 10 seconds (SWR)

**Response:**
```json
{
  "latest_cid": "QmPm7...",
  "rows": 110,
  "last_updated": "2025-10-22T16:48:35Z",
  "encryption": {
    "enabled": true,
    "status": "active"
  }
}
```

#### 2. GET /health
**Purpose:** Backend health check  
**Use:** Error detection, monitoring

**Response:**
```json
{
  "status": "healthy",
  "uptime": 3600,
  "lighthouse": {
    "sdk_version": "0.4.3",
    "endpoint": "https://node.lighthouse.storage"
  }
}
```

---

## 🎨 UI/UX Features

### 1. Real-time Status Updates
- Metadata refreshes every 10 seconds
- Visual indicators for data freshness
- Live row count and timestamp

### 2. Progressive Disclosure
- Wallet connection → Token claiming → Data unlocking
- Each step enabled only when previous step complete
- Clear progress messages at each stage

### 3. Error Handling
- Network errors: "Failed to fetch metadata"
- Wallet errors: "Please install MetaMask"
- Token errors: "Insufficient DADC balance"
- Decryption errors: "Access denied" or specific error

### 4. Visual Feedback
- Loading spinners during async operations
- Success/error messages with color coding
- Transaction hashes as links to Etherscan
- Disabled buttons with explanatory tooltips

---

## 🔧 Key Dependencies

### Production Dependencies
```json
{
  "next": "14.0.4",                    // React framework
  "react": "^18.2.0",                  // UI library
  "react-dom": "^18.2.0",              // DOM rendering
  "@lighthouse-web3/sdk": "^0.3.3",    // Encryption & decryption
  "ethers": "^6.9.0",                  // Blockchain interaction
  "swr": "^2.2.4"                      // Data fetching & caching
}
```

### Why These Versions?

**Lighthouse SDK v0.3.3:**
- Latest stable release
- Supports native encryption
- Access control integration

**ethers.js v6:**
- Modern API (v5 is deprecated)
- Better TypeScript support
- Smaller bundle size

**SWR v2:**
- Auto-refresh
- Cache management
- Error retry logic

---

## 🚀 Deployment

### Local Development
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:3000
```

### Production Build
```bash
npm run build
npm start
```

### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Vercel Configuration:**
- Framework: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`
- Environment Variables: All `NEXT_PUBLIC_*` vars from .env.production

---

## 🔍 Debugging Tips

### 1. Check Browser Console
```javascript
// Enable verbose logging
localStorage.debug = '*'

// Check what Lighthouse SDK is doing
console.log('Decrypted type:', typeof decrypted, decrypted?.constructor?.name)
```

### 2. Network Tab
- Watch for `/metadata` calls (should be every 10s)
- Check CORS headers
- Verify response status codes

### 3. MetaMask Issues
- Ensure connected to Sepolia network
- Check if wallet has ETH for gas
- Clear MetaMask activity data if stuck

### 4. Decryption Failures
Common causes:
- Token balance < 1.0 DADC
- Wrong network (not Sepolia)
- CID not yet uploaded
- Access control not applied yet

---

## 📊 Performance Optimization

### 1. SWR Caching
- Metadata cached for 10 seconds
- Reduces API calls
- Instant navigation if cached

### 2. Code Splitting
- Next.js automatically splits routes
- Lighthouse SDK lazy-loaded
- Reduces initial bundle size

### 3. Image Optimization
- Use Next.js `<Image>` component
- Automatic WebP conversion
- Responsive sizing

---

## 🎓 Key Learnings

### 1. SDK Return Type Handling
Always check return types from third-party SDKs:
```typescript
console.log('Type:', typeof result, result?.constructor?.name)
```

### 2. Async State Management
Use proper loading states:
```typescript
const [isLoading, setIsLoading] = useState(false)

async function action() {
  setIsLoading(true)
  try {
    await doSomething()
  } finally {
    setIsLoading(false)  // Always clean up
  }
}
```

### 3. Error Boundaries
Wrap async operations in try-catch:
```typescript
try {
  const result = await riskyOperation()
} catch (err) {
  console.error('Error:', err)
  setError(err.message)
}
```

---

## 🔗 Related Documentation

- **Backend:** `LIGHTHOUSE_ENCRYPTION_SUCCESS.md`
- **Deployment:** `VERCEL_DEPLOYMENT_FIX.md`
- **Quick Start:** `QUICK_START.md`
- **Frontend/Backend Integration:** `FRONTEND_BACKEND_FIX_SUMMARY.md`

---

## ✅ Current Status

### Working Features
- ✅ Wallet connection (MetaMask)
- ✅ Network detection (Sepolia)
- ✅ Token balance check
- ✅ Token faucet claiming
- ✅ Metadata fetching (auto-refresh)
- ✅ Data decryption with token-gating
- ✅ Blob/ArrayBuffer handling (FIXED!)
- ✅ Download decrypted data
- ✅ FAQ section

### Production Ready
- ✅ Error handling
- ✅ Loading states
- ✅ Responsive design
- ✅ Environment configuration
- ✅ CORS support
- ✅ TypeScript types

---

## 🎯 User Journey

1. **Visit Site** → See metadata (CID, rows, freshness)
2. **Connect Wallet** → MetaMask prompts for connection
3. **Check Balance** → Automatically checks DADC balance
4. **Claim Tokens** → If balance < 1.0, can claim 100 DADC
5. **Unlock Data** → Sign message → Decrypt → View data
6. **Download** → Save decrypted JSONL file locally

**Total Time:** ~2 minutes for first-time user

---

## 📈 Future Enhancements

### Potential Improvements
1. **Multi-file Support** - Decrypt multiple files
2. **Data Visualization** - Charts for DEX arb opportunities
3. **Historical Data** - Browse previous uploads
4. **Batch Downloads** - Download multiple files at once
5. **Mobile Optimization** - Better mobile UX
6. **Progressive Web App** - Offline support
7. **Share Links** - Generate shareable decrypt links

---

## 🏆 Achievement

**Frontend successfully integrates with:**
- ✅ Lighthouse native encryption
- ✅ ERC20 token-gating
- ✅ MetaMask wallet
- ✅ Railway backend API
- ✅ Sepolia testnet

**Hackathon Ready:** All features operational for ETHOnline 2025 🚀
