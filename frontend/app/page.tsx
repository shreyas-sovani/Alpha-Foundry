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
const AGENT_ADDRESS = process.env.NEXT_PUBLIC_AGENT_ADDRESS || '' // Your Agentverse agent address
const DELTAV_API_KEY = process.env.NEXT_PUBLIC_DELTAV_API_KEY || '' // DeltaV API key (optional)

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
  const [showAgentChat, setShowAgentChat] = useState(false)
  
  // Agent chat state
  const [chatMessages, setChatMessages] = useState<Array<{role: 'user' | 'agent', text: string}>>([])
  const [chatInput, setChatInput] = useState('')
  const [isSendingMessage, setIsSendingMessage] = useState(false)
  
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
  
  // Burn 1 DADC token to access data (pay-per-decrypt)
  const burnTokenForAccess = async () => {
    if (!signer || !walletState.address) {
      throw new Error('Wallet not connected')
    }
    
    const currentBalance = parseFloat(walletState.balance || '0')
    if (currentBalance < 1.0) {
      throw new Error('Insufficient balance. You need at least 1 DADC to decrypt.')
    }
    
    const BURN_ADDRESS = '0x000000000000000000000000000000000000dEaD'
    const BURN_AMOUNT = ethers.parseEther('1.0') // 1 DADC
    
    try {
      console.log('🔥 Burning 1 DADC for access...')
      console.log('   Current balance:', currentBalance, 'DADC')
      
      // Create DataCoin contract instance
      const dataCoin = new ethers.Contract(
        DATACOIN_ADDRESS,
        ['function transfer(address to, uint256 amount) returns (bool)'],
        signer
      )
      
      // Execute burn (transfer to dead address)
      const tx = await dataCoin.transfer(BURN_ADDRESS, BURN_AMOUNT)
      console.log('   Transaction submitted:', tx.hash)
      
      setSuccess(`Burning 1 DADC... Tx: ${tx.hash.slice(0, 10)}...${tx.hash.slice(-8)}`)
      
      // Wait for confirmation
      const receipt = await tx.wait()
      console.log('   ✅ Burn confirmed in block:', receipt.blockNumber)
      console.log('   New balance will be:', currentBalance - 1, 'DADC')
      
      // Update balance display
      if (provider && walletState.address) {
        await new Promise(resolve => setTimeout(resolve, 1000)) // Wait for state to update
        await updateWalletState(walletState.address, walletState.chainId!, provider)
      }
      
      return receipt
    } catch (err: any) {
      console.error('❌ Burn failed:', err)
      if (err.code === 'ACTION_REJECTED' || err.message?.includes('user rejected')) {
        throw new Error('Transaction cancelled by user')
      }
      throw new Error(`Failed to burn tokens: ${err.message}`)
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
      
      // 🔥 Step 1: Burn 1 DADC for access (NEW!)
      setSuccess('Step 1/4: Burning 1 DADC for access...')
      
      const currentBalance = parseFloat(walletState.balance || '0')
      console.log('   Current balance:', currentBalance, 'DADC')
      
      if (currentBalance < 1.0) {
        throw new Error('Insufficient balance. You need at least 1 DADC to decrypt.')
      }
      
      await burnTokenForAccess()
      
      const remainingBalance = currentBalance - 1
      console.log('   ✅ 1 DADC burned, remaining:', remainingBalance, 'DADC')
      console.log('   → You have', Math.floor(remainingBalance), 'decrypts left')
      
      // Step 2: Get signed message for Lighthouse access control
      setSuccess(`Step 2/4: Requesting signature... (${Math.floor(remainingBalance)} decrypts remaining)`)
      
      const address = walletState.address!
      const messageRequested: any = await lighthouse.getAuthMessage(address)
      
      console.log('   Message to sign:', messageRequested)
      
      // Step 3: Sign the message
      setSuccess('Step 3/4: Please sign the message in MetaMask...')
      
      // Access the message from the response (could be .message or direct string)
      const messageToSign = typeof messageRequested === 'string' 
        ? messageRequested 
        : messageRequested.message || messageRequested.data?.message || messageRequested
      
      const signedMessage = await signer.signMessage(messageToSign)
      
      console.log('   ✅ Message signed')
      
      // Step 4: Fetch decryption key (Lighthouse will check ERC20 balance)
      setSuccess('Step 4/4: Fetching decryption key (verifying balance)...')
      
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
      
      // Show success with remaining balance
      const finalBalance = currentBalance - 1
      setSuccess(
        `🎉 Data unlocked! 1 DADC burned. You have ${Math.floor(finalBalance)} decrypt${Math.floor(finalBalance) === 1 ? '' : 's'} remaining.`
      )
      
    } catch (err: any) {
      console.error('❌ Decryption error:', err)
      
      if (err.message?.includes('access control')) {
        setError('Access denied: Your wallet does not have sufficient DADC tokens.')
      } else if (err.message?.includes('not found')) {
        setError('Encrypted file not found on Lighthouse. It may still be uploading.')
      } else if (err.message?.includes('Insufficient balance')) {
        setError(err.message)
      } else if (err.message?.includes('cancelled') || err.message?.includes('rejected')) {
        setError('Transaction cancelled by user.')
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
  
  // Agent chat: Send message to Agentverse hosted agent
  const sendChatMessage = async () => {
    if (!chatInput.trim() || isSendingMessage || !AGENT_ADDRESS) return
    
    const userMessage = chatInput.trim()
    setChatInput('')
    
    // Add user message
    setChatMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setIsSendingMessage(true)
    
    try {
      // Call the Agentverse agent via HTTP POST
      // Your agent should expose an HTTP endpoint that accepts messages
      const agentUrl = `https://agentverse.ai/v1/agents/agent1qfaxddhl2eqg4de26pvhcvsja3j7rz7wwh0da5t58cvyws9rq9q36zrvesd/submit`
      
      const response = await fetch(agentUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(DELTAV_API_KEY && { 'Authorization': `Bearer ${DELTAV_API_KEY}` })
        },
        body: JSON.stringify({
          message: userMessage,
          context: {
            metadata_endpoint: `${METADATA_API}/metadata`,
            preview_endpoint: `${METADATA_API}/preview`
          }
        })
      })
      
      if (!response.ok) {
        throw new Error(`Agent responded with status ${response.status}`)
      }
      
      const data = await response.json()
      
      // Extract agent's response
      const agentResponse = data.response || data.message || data.text || 'Agent did not provide a response.'
      
      // Add agent response
      setChatMessages(prev => [...prev, { role: 'agent', text: agentResponse }])
      
    } catch (err: any) {
      console.error('Agent communication error:', err)
      
      // Fallback: If agent is not reachable, provide helpful error
      const errorMessage = `⚠️ Cannot reach agent. Error: ${err.message}\n\nPlease ensure:\n1. Agent address is configured\n2. Agent is running on Agentverse\n3. Agent HTTP endpoint is accessible`
      
      setChatMessages(prev => [...prev, { 
        role: 'agent', 
        text: errorMessage
      }])
    } finally {
      setIsSendingMessage(false)
    }
  }
  
  // Initialize chat with welcome message
  useEffect(() => {
    if (showAgentChat && chatMessages.length === 0 && AGENT_ADDRESS) {
      setChatMessages([{
        role: 'agent',
        text: `👋 Hi! I'm your DEXArb AI agent hosted on Agentverse.\n\nI can analyze the latest arbitrage data and provide insights.\n\nAgent Address: ${AGENT_ADDRESS.substring(0, 12)}...${AGENT_ADDRESS.substring(AGENT_ADDRESS.length - 8)}\n\nAsk me anything about the data!`
      }])
    } else if (showAgentChat && !AGENT_ADDRESS) {
      setChatMessages([{
        role: 'agent',
        text: `⚠️ Agent not configured!\n\nPlease set NEXT_PUBLIC_AGENT_ADDRESS in your environment variables.\n\nGet your agent address from: https://agentverse.ai`
      }])
    }
  }, [showAgentChat])
  
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
                      <div className="text-xs text-gray-400 mt-1">
                        ≈ {Math.floor(parseFloat(walletState.balance))} decrypt{Math.floor(parseFloat(walletState.balance)) === 1 ? '' : 's'} available
                      </div>
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
            
            {/* Cost Warning */}
            {!decryptedData && (
              <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 mb-4">
                <p className="text-yellow-300 font-semibold mb-2">
                  🔥 Cost: 1 DADC per decrypt
                </p>
                <p className="text-sm text-gray-300">
                  Clicking "Unlock & Decrypt" will burn 1 DADC token (non-refundable). 
                  You have <strong>{Math.floor(parseFloat(walletState.balance || '0'))} decrypt{Math.floor(parseFloat(walletState.balance || '0')) === 1 ? '' : 's'}</strong> available 
                  with your current balance.
                </p>
              </div>
            )}
            
            <p className="text-gray-300 mb-6">
              {!decryptedData ? 
                'Ready to access encrypted data! The decryption process will:' :
                'Data successfully decrypted! You can download the full file below.'
              }
            </p>
            
            {!decryptedData && (
              <ul className="text-gray-300 text-sm list-disc list-inside mb-6 space-y-1">
                <li>Burn 1 DADC token to 0xdead address</li>
                <li>Verify your balance on Sepolia blockchain</li>
                <li>Decrypt the data using Lighthouse SDK</li>
                <li>Display the decrypted JSONL content</li>
              </ul>
            )}
            
            {!decryptedData ? (
              <button
                onClick={unlockData}
                disabled={isDecrypting}
                className="btn-primary text-lg px-8 py-4 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDecrypting ? '🔄 Decrypting...' : '� Burn 1 DADC & Unlock Data'}
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
                  1. You burn 1 DADC token (sent to 0xdead address)<br />
                  2. You sign a message to prove wallet ownership (no gas)<br />
                  3. Lighthouse checks your remaining DADC balance<br />
                  4. If balance ≥1 DADC, you receive the decryption key<br />
                  5. Data is decrypted in your browser<br />
                  6. You can download the full JSONL file
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">Why burn tokens?</h3>
                <p className="text-gray-300">
                  Pay-per-decrypt model: 1 DADC = 1 decryption access. Burning tokens creates scarcity 
                  and deflationary pressure. With 100 DADC, you get exactly 100 decryptions. 
                  Track burns on-chain at{' '}
                  <a href="https://sepolia.etherscan.io/address/0x000000000000000000000000000000000000dEaD" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
                    0xdead
                  </a>.
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg mb-2">Is my data secure?</h3>
                <p className="text-gray-300">
                  Yes! The data is encrypted with Lighthouse native encryption and stored on IPFS.
                  Only wallets with ≥1 DADC token can decrypt it. Your private keys never leave your browser.
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
      
      {/* Agentverse Chat Widget - Floating Button */}
      {metadata && (
        <>
          {/* Chat Toggle Button */}
          <button
            onClick={() => setShowAgentChat(!showAgentChat)}
            className="fixed bottom-6 right-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-110 z-50"
            title="Chat with AI Assistant"
          >
            {showAgentChat ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            )}
          </button>
          
          {/* Chat Window */}
          {showAgentChat && (
            <div className="fixed bottom-24 right-6 w-96 h-[600px] bg-gray-900 border-2 border-blue-500 rounded-lg shadow-2xl z-50 flex flex-col">
              {/* Chat Header */}
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4 rounded-t-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                      🤖
                    </div>
                    <div>
                      <h3 className="font-bold text-white">DEXArb AI Assistant</h3>
                      <p className="text-xs text-gray-200">Real-time Data Insights</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowAgentChat(false)}
                    className="text-white hover:text-gray-300"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              
              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-800 text-gray-100'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                    </div>
                  </div>
                ))}
                {isSendingMessage && (
                  <div className="flex justify-start">
                    <div className="bg-gray-800 rounded-lg p-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Chat Input */}
              <div className="border-t border-gray-700 p-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                    placeholder="Ask about data, stats, encryption..."
                    className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isSendingMessage}
                  />
                  <button
                    onClick={sendChatMessage}
                    disabled={!chatInput.trim() || isSendingMessage}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
                  >
                    Send
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Try: "How many rows?", "Show latest", "Help"
                </p>
              </div>
            </div>
          )}
        </>
      )}
    </main>
  )
}
