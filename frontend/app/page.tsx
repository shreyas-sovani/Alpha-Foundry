'use client'

import { useState, useEffect, useCallback } from 'react'
import { ethers } from 'ethers'
import useSWR from 'swr'

// Import Lighthouse SDK
// @ts-ignore - Lighthouse SDK types may not be perfect
import lighthouse from '@lighthouse-web3/sdk'

// Configuration from environment
const METADATA_API = process.env.NEXT_PUBLIC_METADATA_API || 'http://localhost:8787'
const CHAIN_ID = parseInt(process.env.NEXT_PUBLIC_CHAIN_ID || '11155111')
const CHAIN_NAME = process.env.NEXT_PUBLIC_CHAIN_NAME || 'Sepolia'
const RPC_URL = process.env.NEXT_PUBLIC_RPC_URL || 'https://ethereum-sepolia-rpc.publicnode.com'
const DATACOIN_ADDRESS = process.env.NEXT_PUBLIC_DATACOIN_ADDRESS || '0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC'
const FAUCET_ADDRESS = process.env.NEXT_PUBLIC_FAUCET_ADDRESS || '0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB'
const MIN_BALANCE = parseFloat(process.env.NEXT_PUBLIC_MIN_BALANCE || '1.0')

// Minimal ABIs
const DATACOIN_ABI = [
  'function balanceOf(address account) view returns (uint256)',
  'function name() view returns (string)',
  'function symbol() view returns (string)',
  'function decimals() view returns (uint8)'
]

const FAUCET_ABI = [
  'function claimTokens() external',
  'function hasClaimed(address account) view returns (bool)',
  'function CLAIM_AMOUNT() view returns (uint256)'
]

// Types
interface Metadata {
  latest_cid: string | null
  data_coin_address?: string
  last_updated?: string
  rows?: number
  freshness_minutes?: number
  format?: string
  fields?: any
  lighthouse_gateway?: string
  encryption?: {
    enabled: boolean
    algorithm: string
    status: string
  }
}

interface WalletState {
  address: string | null
  chainId: number | null
  balance: string | null
  hasClaimed: boolean
  isEligible: boolean
}

// Fetcher for SWR with better error handling
const fetcher = async (url: string) => {
  console.log('Fetching from:', url)
  const response = await fetch(url)
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error('Fetch failed:', response.status, errorText)
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }
  
  const data = await response.json()
  console.log('Fetched metadata successfully:', data)
  return data
}

export default function UnlockPage() {
  // Wallet state
  const [walletState, setWalletState] = useState<WalletState>({
    address: null,
    chainId: null,
    balance: null,
    hasClaimed: false,
    isEligible: false,
  })
  
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null)
  const [signer, setSigner] = useState<ethers.Signer | null>(null)
  
  // UI state
  const [isConnecting, setIsConnecting] = useState(false)
  const [isClaiming, setIsClaiming] = useState(false)
  const [isDecrypting, setIsDecrypting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [decryptedData, setDecryptedData] = useState<string | null>(null)
  const [showFAQ, setShowFAQ] = useState(false)
  
  // Fetch metadata from backend
  const { data: metadata, error: metadataError, mutate: refetchMetadata } = useSWR<Metadata>(
    `${METADATA_API}/metadata`,
    fetcher,
    { refreshInterval: 10000 } // Refresh every 10 seconds
  )
  
  // Check if wallet is connected on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && window.ethereum) {
      checkConnection()
    }
  }, [])
  
  // Check wallet connection status
  const checkConnection = async () => {
    try {
      if (!window.ethereum) return
      
      const provider = new ethers.BrowserProvider(window.ethereum)
      const accounts = await provider.listAccounts()
      
      if (accounts.length > 0) {
        const signer = await provider.getSigner()
        const address = await signer.getAddress()
        const network = await provider.getNetwork()
        
        setProvider(provider)
        setSigner(signer)
        
        await updateWalletState(address, Number(network.chainId), provider)
      }
    } catch (err) {
      console.error('Error checking connection:', err)
    }
  }
  
  // Update wallet state (balance, eligibility, etc.)
  const updateWalletState = async (
    address: string,
    chainId: number,
    provider: ethers.BrowserProvider
  ) => {
    try {
      // Check if on correct network
      if (chainId !== CHAIN_ID) {
        setWalletState({
          address,
          chainId,
          balance: null,
          hasClaimed: false,
          isEligible: false,
        })
        return
      }
      
      // Get DataCoin balance
      const dataCoin = new ethers.Contract(DATACOIN_ADDRESS, DATACOIN_ABI, provider)
      const balance = await dataCoin.balanceOf(address)
      const decimals = await dataCoin.decimals()
      const balanceFormatted = ethers.formatUnits(balance, decimals)
      
      // Check if claimed from faucet
      const faucet = new ethers.Contract(FAUCET_ADDRESS, FAUCET_ABI, provider)
      const hasClaimed = await faucet.hasClaimed(address)
      
      // Check if eligible (balance >= minimum)
      const isEligible = parseFloat(balanceFormatted) >= MIN_BALANCE
      
      setWalletState({
        address,
        chainId,
        balance: balanceFormatted,
        hasClaimed,
        isEligible,
      })
      
      if (isEligible) {
        setError(null)
        setSuccess(`✅ You have ${balanceFormatted} DADC tokens. You can unlock the data!`)
      }
    } catch (err: any) {
      console.error('Error updating wallet state:', err)
      setError(`Failed to check wallet state: ${err.message}`)
    }
  }
  
  // Connect wallet
  const connectWallet = async () => {
    setIsConnecting(true)
    setError(null)
    setSuccess(null)
    
    try {
      if (!window.ethereum) {
        throw new Error('MetaMask not installed. Please install MetaMask to continue.')
      }
      
      const provider = new ethers.BrowserProvider(window.ethereum)
      
      // Request account access
      await window.ethereum.request({ method: 'eth_requestAccounts' })
      
      const signer = await provider.getSigner()
      const address = await signer.getAddress()
      const network = await provider.getNetwork()
      
      setProvider(provider)
      setSigner(signer)
      
      // Check if on Sepolia
      if (Number(network.chainId) !== CHAIN_ID) {
        // Try to switch network
        try {
          await window.ethereum.request({
            method: 'wallet_switchEthereumChain',
            params: [{ chainId: `0x${CHAIN_ID.toString(16)}` }],
          })
          
          // Re-fetch network after switch
          const newNetwork = await provider.getNetwork()
          await updateWalletState(address, Number(newNetwork.chainId), provider)
        } catch (switchError: any) {
          if (switchError.code === 4902) {
            throw new Error(`Please add ${CHAIN_NAME} network to MetaMask manually.`)
          }
          throw new Error(`Please switch to ${CHAIN_NAME} network in MetaMask.`)
        }
      } else {
        await updateWalletState(address, Number(network.chainId), provider)
      }
      
      setSuccess(`Connected to ${address.slice(0, 6)}...${address.slice(-4)}`)
    } catch (err: any) {
      console.error('Connection error:', err)
      setError(err.message || 'Failed to connect wallet')
    } finally {
      setIsConnecting(false)
    }
  }
  
  // Claim tokens from faucet
  const claimTokens = async () => {
    if (!signer || !walletState.address) {
      setError('Please connect your wallet first')
      return
    }
    
    setIsClaiming(true)
    setError(null)
    setSuccess(null)
    
    try {
      const faucet = new ethers.Contract(FAUCET_ADDRESS, FAUCET_ABI, signer)
      
      console.log('🚰 Claiming tokens from faucet...')
      const tx = await faucet.claimTokens()
      
      setSuccess(`Transaction submitted: ${tx.hash}`)
      console.log('⏳ Waiting for confirmation...')
      
      const receipt = await tx.wait()
      console.log('✅ Transaction confirmed:', receipt.hash)
      
      setSuccess(`✅ Claimed 100 DADC tokens! Refreshing balance...`)
      
      // Wait a bit for blockchain state to update
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Refresh wallet state
      if (provider && walletState.address) {
        await updateWalletState(walletState.address, walletState.chainId!, provider)
      }
      
      setSuccess(`✅ Success! You now have DADC tokens. You can unlock the data below.`)
    } catch (err: any) {
      console.error('Claim error:', err)
      
      if (err.message?.includes('AlreadyClaimed')) {
        setError('You have already claimed tokens from this faucet.')
      } else {
        setError(`Failed to claim tokens: ${err.message}`)
      }
    } finally {
      setIsClaiming(false)
    }
  }
  
  // Unlock and decrypt data using Lighthouse SDK
  const unlockData = async () => {
    if (!walletState.isEligible) {
      setError('You need at least 1 DADC token to unlock the data. Please claim tokens first.')
      return
    }
    
    if (!metadata?.latest_cid) {
      setError('No encrypted data available yet. Please try again later.')
      return
    }
    
    if (!signer) {
      setError('Please connect your wallet first')
      return
    }
    
    setIsDecrypting(true)
    setError(null)
    setSuccess(null)
    setDecryptedData(null)
    
    try {
      console.log('🔓 Starting decryption process...')
      console.log('   CID:', metadata.latest_cid)
      console.log('   Wallet:', walletState.address)
      console.log('   Balance:', walletState.balance, 'DADC')
      
      // Step 1: Get signed message for Lighthouse access control
      setSuccess('Step 1/3: Requesting signature for access control...')
      
      const address = walletState.address!
      const messageRequested: any = await lighthouse.getAuthMessage(address)
      
      console.log('   Message to sign:', messageRequested)
      
      // Step 2: Sign the message
      setSuccess('Step 2/3: Please sign the message in MetaMask...')
      
      // Access the message from the response (could be .message or direct string)
      const messageToSign = typeof messageRequested === 'string' 
        ? messageRequested 
        : messageRequested.message || messageRequested.data?.message || messageRequested
      
      const signedMessage = await signer.signMessage(messageToSign)
      
      console.log('   ✅ Message signed')
      
      // Step 3: Fetch decryption key (Lighthouse will check ERC20 balance)
      setSuccess('Step 3/3: Fetching decryption key (checking token balance)...')
      
      const keyObject: any = await lighthouse.fetchEncryptionKey(
        metadata.latest_cid,
        address,
        signedMessage
      )
      
      console.log('   ✅ Decryption key retrieved')
      
      // Step 4: Download and decrypt the file
      setSuccess('Downloading and decrypting data...')
      
      // Extract the key (handle different response structures)
      const decryptionKey = keyObject?.data?.key || keyObject?.key
      if (!decryptionKey) {
        throw new Error('Failed to retrieve decryption key from Lighthouse')
      }
      
      const decrypted = await lighthouse.decryptFile(
        metadata.latest_cid,
        decryptionKey
      )
      
      console.log('   ✅ File decrypted successfully')
      console.log('   Decrypted type:', typeof decrypted, decrypted?.constructor?.name)
      
      // Convert decrypted data to string (handle Blob, ArrayBuffer, or direct string)
      let decryptedText: string
      
      if (typeof decrypted === 'string') {
        decryptedText = decrypted
      } else if (decrypted instanceof Blob) {
        // If it's a Blob, read it as text
        decryptedText = await decrypted.text()
      } else if (decrypted instanceof ArrayBuffer) {
        // If it's an ArrayBuffer, decode to string
        decryptedText = new TextDecoder().decode(decrypted)
      } else if (decrypted?.data) {
        // If wrapped in object with .data property
        const data = decrypted.data
        if (typeof data === 'string') {
          decryptedText = data
        } else if (data instanceof Blob) {
          decryptedText = await data.text()
        } else {
          decryptedText = JSON.stringify(data, null, 2)
        }
      } else {
        // Fallback: try to convert to string
        decryptedText = String(decrypted)
      }
      
      console.log('   Decrypted data preview:', decryptedText.substring(0, 200))
      
      setDecryptedData(decryptedText)
      setSuccess('🎉 Data unlocked and decrypted successfully!')
      
    } catch (err: any) {
      console.error('❌ Decryption error:', err)
      
      if (err.message?.includes('access control')) {
        setError('Access denied: Your wallet does not have sufficient DADC tokens.')
      } else if (err.message?.includes('not found')) {
        setError('Encrypted file not found on Lighthouse. It may still be uploading.')
      } else {
        setError(`Failed to decrypt data: ${err.message}`)
      }
    } finally {
      setIsDecrypting(false)
    }
  }
  
  // Download decrypted data as file
  const downloadData = () => {
    if (!decryptedData) return
    
    const blob = new Blob([decryptedData], { type: 'application/x-ndjson' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dexarb_decrypted_${Date.now()}.jsonl`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    setSuccess('✅ Downloaded decrypted data!')
  }
  
  // Render
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 gradient-text">
            DEXArb Data Unlock
          </h1>
          <p className="text-xl text-gray-300">
            Token-Gated Encrypted Data Access via Lighthouse Storage
          </p>
          <p className="text-sm text-gray-400 mt-2">
            ETHOnline 2025 • Sepolia Testnet
          </p>
        </div>
        
        {/* Network/Wallet Status Card */}
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">🔐 Wallet Status</h2>
            {!walletState.address ? (
              <button
                onClick={connectWallet}
                disabled={isConnecting}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isConnecting ? '⏳ Connecting...' : '🔌 Connect Wallet'}
              </button>
            ) : (
              <div className="text-right">
                <div className="text-sm text-gray-400">Connected</div>
                <div className="font-mono text-sm">
                  {walletState.address.slice(0, 6)}...{walletState.address.slice(-4)}
                </div>
              </div>
            )}
          </div>
          
          {walletState.address && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-700/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Network</div>
                <div className="font-semibold">
                  {walletState.chainId === CHAIN_ID ? (
                    <span className="status-badge status-success">
                      ✅ {CHAIN_NAME}
                    </span>
                  ) : (
                    <span className="status-badge status-error">
                      ❌ Wrong Network
                    </span>
                  )}
                </div>
              </div>
              
              <div className="bg-gray-700/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">DADC Balance</div>
                <div className="font-semibold">
                  {walletState.balance ? (
                    <span>
                      {parseFloat(walletState.balance).toFixed(2)} DADC
                    </span>
                  ) : (
                    <span className="text-gray-500">Loading...</span>
                  )}
                </div>
              </div>
              
              <div className="bg-gray-700/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Access Status</div>
                <div className="font-semibold">
                  {walletState.isEligible ? (
                    <span className="status-badge status-success">
                      ✅ Eligible
                    </span>
                  ) : (
                    <span className="status-badge status-warning">
                      ⚠️ Need Tokens
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {walletState.address && walletState.chainId !== CHAIN_ID && (
            <div className="mt-4 p-4 bg-red-900/30 border border-red-700 rounded-lg">
              <p className="text-red-300">
                ⚠️ Wrong network detected. Please switch to <strong>{CHAIN_NAME}</strong> in MetaMask.
              </p>
            </div>
          )}
        </div>
        
        {/* Claim Tokens Section */}
        {walletState.address && !walletState.isEligible && walletState.chainId === CHAIN_ID && (
          <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 backdrop-blur rounded-xl p-6 mb-6 border border-blue-700">
            <h2 className="text-2xl font-bold mb-4">🪙 Claim DADC Tokens</h2>
            <p className="text-gray-300 mb-4">
              You need at least <strong>{MIN_BALANCE} DADC</strong> token to access the encrypted data.
              {walletState.hasClaimed ? (
                <span className="text-yellow-300"> You've already claimed from this wallet.</span>
              ) : (
                <span className="text-green-300"> Claim 100 DADC tokens for free!</span>
              )}
            </p>
            
            {!walletState.hasClaimed ? (
              <div className="space-y-4">
                <button
                  onClick={claimTokens}
                  disabled={isClaiming}
                  className="btn-primary w-full md:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isClaiming ? '⏳ Claiming...' : '🎁 Claim 100 DADC Tokens'}
                </button>
                
                <div className="text-sm text-gray-400">
                  <p>Or claim via Etherscan:</p>
                  <a
                    href={`https://sepolia.etherscan.io/address/${FAUCET_ADDRESS}#writeContract`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 underline"
                  >
                    {FAUCET_ADDRESS}
                  </a>
                </div>
              </div>
            ) : (
              <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
                <p className="text-yellow-300">
                  ℹ️ You've already claimed tokens. Try refreshing your balance above, or use a different wallet.
                </p>
              </div>
            )}
          </div>
        )}
        
        {/* Data Info Card */}
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">📊 Encrypted Data Feed</h2>
            <div className="text-xs text-gray-500 font-mono">
              API: {METADATA_API}
            </div>
          </div>
          
          {metadataError ? (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
              <p className="text-red-300">
                ❌ Failed to load metadata from backend: {metadataError.message}
              </p>
            </div>
          ) : !metadata ? (
            <div className="text-gray-400">
              ⏳ Loading metadata...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Latest CID</div>
                  <div className="font-mono text-sm break-all">
                    {metadata.latest_cid || (
                      <span className="text-yellow-300">Not uploaded yet</span>
                    )}
                  </div>
                </div>
                
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Last Updated</div>
                  <div className="font-semibold">
                    {metadata.last_updated ? (
                      new Date(metadata.last_updated).toLocaleString()
                    ) : (
                      <span className="text-gray-500">N/A</span>
                    )}
                  </div>
                </div>
                
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Total Rows</div>
                  <div className="font-semibold">
                    {metadata.rows?.toLocaleString() || 'N/A'}
                  </div>
                </div>
                
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">Freshness</div>
                  <div className="font-semibold">
                    {metadata.freshness_minutes !== undefined ? (
                      <span>~{metadata.freshness_minutes} minutes ago</span>
                    ) : (
                      <span className="text-gray-500">N/A</span>
                    )}
                  </div>
                </div>
              </div>
              
              {metadata.encryption && (
                <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🔐</span>
                    <span className="font-semibold">Encryption Enabled</span>
                  </div>
                  <div className="text-sm text-gray-300 space-y-1">
                    <p>• Algorithm: {metadata.encryption.algorithm}</p>
                    <p>• Status: {metadata.encryption.status}</p>
                    <p>• Access: Token-gated (≥{MIN_BALANCE} DADC required)</p>
                  </div>
                </div>
              )}
              
              <div className="bg-gray-700/50 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-2">Data Format</div>
                <div className="text-sm text-gray-300">
                  <p>• Format: <code className="bg-gray-900 px-2 py-1 rounded">{metadata.format || 'JSONL'}</code></p>
                  <p>• Schema: DEX swap events with arbitrage detection</p>
                  <p>• Window: Rolling 24-hour price tracking</p>
                  <p>• Chains: Base, Ethereum, Polygon</p>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Unlock/Decrypt Section */}
        {walletState.isEligible && metadata?.latest_cid && (
          <div className="bg-gradient-to-r from-green-900/50 to-blue-900/50 backdrop-blur rounded-xl p-6 mb-6 border border-green-700">
            <h2 className="text-2xl font-bold mb-4">🔓 Unlock & Decrypt Data</h2>
            <p className="text-gray-300 mb-6">
              You're eligible to access the encrypted data! Click below to decrypt using Lighthouse SDK.
            </p>
            
            {!decryptedData ? (
              <button
                onClick={unlockData}
                disabled={isDecrypting}
                className="btn-primary text-lg px-8 py-4 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDecrypting ? '🔄 Decrypting...' : '🔓 Unlock & Decrypt Data'}
              </button>
            ) : (
              <div className="space-y-4">
                <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                  <p className="text-green-300 font-semibold mb-2">
                    ✅ Data decrypted successfully!
                  </p>
                  <p className="text-sm text-gray-300">
                    Preview (first 500 chars):
                  </p>
                  <pre className="mt-2 bg-gray-900 p-4 rounded-lg text-xs overflow-x-auto max-h-64 overflow-y-auto">
                    {decryptedData.substring(0, 500)}...
                  </pre>
                </div>
                
                <div className="flex gap-4">
                  <button
                    onClick={downloadData}
                    className="btn-primary"
                  >
                    💾 Download Full Data
                  </button>
                  <button
                    onClick={() => setDecryptedData(null)}
                    className="btn-secondary"
                  >
                    🔄 Decrypt Again
                  </button>
                </div>
                
                <div className="text-sm text-gray-400">
                  <p>✓ Total size: {(decryptedData.length / 1024).toFixed(2)} KB</p>
                  <p>✓ Lines: {decryptedData.split('\n').length.toLocaleString()}</p>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Status Messages */}
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
            <p className="text-red-300">{error}</p>
          </div>
        )}
        
        {success && !error && (
          <div className="bg-green-900/50 border border-green-700 rounded-lg p-4 mb-6">
            <p className="text-green-300">{success}</p>
          </div>
        )}
        
        {/* FAQ Section */}
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
          <button
            onClick={() => setShowFAQ(!showFAQ)}
            className="flex items-center justify-between w-full text-left"
          >
            <h2 className="text-2xl font-bold">❓ FAQ & Troubleshooting</h2>
            <span className="text-2xl">{showFAQ ? '▼' : '▶'}</span>
          </button>
          
          {showFAQ && (
            <div className="mt-6 space-y-4 text-sm">
              <div>
                <h3 className="font-semibold text-lg mb-2">How do I claim tokens?</h3>
                <p className="text-gray-300">
                  1. Connect your wallet to Sepolia testnet<br />
                  2. Click "Claim 100 DADC Tokens" button<br />
                  3. Confirm the transaction in MetaMask<br />
                  4. Wait for confirmation (~15 seconds)<br />
                  5. Your balance will update automatically
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">What happens when I unlock data?</h3>
                <p className="text-gray-300">
                  1. You'll be asked to sign a message (no gas fee)<br />
                  2. Lighthouse checks your DADC token balance<br />
                  3. If eligible, you receive the decryption key<br />
                  4. Data is decrypted in your browser<br />
                  5. You can download the full JSONL file
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">Is my data secure?</h3>
                <p className="text-gray-300">
                  Yes! The data is encrypted with AES-256-GCM and stored on Lighthouse (IPFS).
                  Only wallets holding ≥1 DADC token can decrypt it. Your private keys never leave your browser.
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">Troubleshooting</h3>
                <ul className="text-gray-300 list-disc list-inside space-y-1">
                  <li>Wrong network? Click your MetaMask extension and switch to Sepolia</li>
                  <li>Transaction failed? Check you have Sepolia ETH for gas</li>
                  <li>Can't decrypt? Ensure you have ≥1 DADC token</li>
                  <li>No data available? The backend may still be uploading (check back in 5 min)</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">Contract Addresses</h3>
                <div className="font-mono text-xs space-y-1 text-gray-300">
                  <p>DataCoin: <a href={`https://sepolia.etherscan.io/address/${DATACOIN_ADDRESS}`} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{DATACOIN_ADDRESS}</a></p>
                  <p>Faucet: <a href={`https://sepolia.etherscan.io/address/${FAUCET_ADDRESS}`} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{FAUCET_ADDRESS}</a></p>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-400">
          <p>Built for ETHOnline 2025 • Powered by Lighthouse Storage & 1MB.io</p>
          <p className="mt-2">
            <a href="https://github.com/shreyas-sovani/Alpha-Foundry" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
              View on GitHub
            </a>
          </p>
        </div>
      </div>
    </main>
  )
}
