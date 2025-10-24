'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { ethers } from 'ethers'
import useSWR from 'swr'
import { motion, useScroll, useTransform, useSpring, useInView, AnimatePresence } from 'framer-motion'
import { useInView as useInViewHook } from 'react-intersection-observer'

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
const AGENT_ADDRESS = process.env.NEXT_PUBLIC_AGENT_ADDRESS || ''
const DELTAV_API_KEY = process.env.NEXT_PUBLIC_DELTAV_API_KEY || ''

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

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 60 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.6, ease: [0.6, -0.05, 0.01, 0.99] }
  }
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.3
    }
  }
}

const scaleIn = {
  hidden: { scale: 0.8, opacity: 0 },
  visible: { 
    scale: 1, 
    opacity: 1,
    transition: { duration: 0.5, ease: "easeOut" }
  }
}

const slideInLeft = {
  hidden: { x: -100, opacity: 0 },
  visible: { 
    x: 0, 
    opacity: 1,
    transition: { duration: 0.6, ease: "easeOut" }
  }
}

const slideInRight = {
  hidden: { x: 100, opacity: 0 },
  visible: { 
    x: 0, 
    opacity: 1,
    transition: { duration: 0.6, ease: "easeOut" }
  }
}

// Magnetic Button Component
const MagneticButton = ({ children, className, onClick, disabled }: any) => {
  const ref = useRef<HTMLButtonElement>(null)
  const [position, setPosition] = useState({ x: 0, y: 0 })

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!ref.current || disabled) return
    const rect = ref.current.getBoundingClientRect()
    const x = e.clientX - rect.left - rect.width / 2
    const y = e.clientY - rect.top - rect.height / 2
    setPosition({ x: x * 0.3, y: y * 0.3 })
  }

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 })
  }

  return (
    <motion.button
      ref={ref}
      className={className}
      onClick={onClick}
      disabled={disabled}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: position.x, y: position.y }}
      transition={{ type: "spring", stiffness: 150, damping: 15, mass: 0.1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {children}
    </motion.button>
  )
}

// Shimmer Effect Component
const ShimmerCard = ({ children, className }: any) => {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      {children}
    </div>
  )
}

// Fetcher for SWR
const fetcher = async (url: string) => {
  const response = await fetch(url)
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText}`)
  }
  return response.json()
}

export default function UnlockPage() {
  // ... (keeping all the existing state and functions - I'll add them in the actual implementation)
  const [walletState, setWalletState] = useState<WalletState>({
    address: null,
    chainId: null,
    balance: null,
    hasClaimed: false,
    isEligible: false,
  })
  
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null)
  const [signer, setSigner] = useState<ethers.Signer | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isClaiming, setIsClaiming] = useState(false)
  const [isDecrypting, setIsDecrypting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [decryptedData, setDecryptedData] = useState<string | null>(null)
  const [showFAQ, setShowFAQ] = useState(false)
  const [showAgentChat, setShowAgentChat] = useState(false)
  const [chatMessages, setChatMessages] = useState<Array<{role: 'user' | 'agent', text: string}>>([])
  const [chatInput, setChatInput] = useState('')
  const [isSendingMessage, setIsSendingMessage] = useState(false)
  
  const { data: metadata, error: metadataError, mutate: refetchMetadata } = useSWR<Metadata>(
    `${METADATA_API}/metadata`,
    fetcher,
    { refreshInterval: 30000 }
  )

  // Scroll progress
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  })

  // Intersection observers for scroll animations
  const [heroRef, heroInView] = useInViewHook({ threshold: 0.3, triggerOnce: true })
  const [walletRef, walletInView] = useInViewHook({ threshold: 0.3, triggerOnce: true })
  const [dataRef, dataInView] = useInViewHook({ threshold: 0.3, triggerOnce: true })

  // Placeholder functions (you'll need to add all your existing logic here)
  useEffect(() => {
    if (typeof window !== 'undefined' && window.ethereum) {
      checkConnection()
    }
  }, [])

  const checkConnection = async () => {
    // ... existing logic
  }

  const updateWalletState = async (address: string, chainId: number, provider: ethers.BrowserProvider) => {
    // ... existing logic
  }

  const connectWallet = async () => {
    // ... existing logic
  }

  const claimTokens = async () => {
    // ... existing logic
  }

  const burnTokenForAccess = async () => {
    // ... existing logic
  }

  const unlockData = async () => {
    // ... existing logic
  }

  const downloadData = () => {
    // ... existing logic
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950 to-purple-950 text-white relative overflow-hidden">
      {/* Scroll Progress Bar */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 origin-left z-50"
        style={{ scaleX }}
      />

      {/* Animated Background Orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div 
          className="absolute top-20 left-10 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            x: [0, 50, 0],
            y: [0, 30, 0],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div 
          className="absolute top-40 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            x: [0, -30, 0],
            y: [0, 50, 0],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        />
        <motion.div 
          className="absolute bottom-20 left-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.15, 1],
            x: [0, 40, 0],
            y: [0, -40, 0],
          }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        />
      </div>

      <div className="container mx-auto px-4 py-12 max-w-7xl relative z-10">
        {/* Hero Section */}
        <motion.div 
          ref={heroRef}
          initial="hidden"
          animate={heroInView ? "visible" : "hidden"}
          variants={staggerContainer}
          className="text-center mb-16 space-y-6"
        >
          {/* Banner with Parallax */}
          <motion.div 
            variants={scaleIn}
            className="relative w-full mb-8"
          >
            <div className="relative h-64 md:h-80 lg:h-96 rounded-3xl overflow-hidden shadow-2xl">
              <motion.img 
                src="/banner.png" 
                alt="Alpha Foundry Banner" 
                className="w-full h-full object-cover object-center"
                initial={{ scale: 1.2 }}
                animate={{ scale: 1 }}
                transition={{ duration: 1.5, ease: "easeOut" }}
              />
              <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-950/40 to-gray-950/90"></div>
            </div>
            
            {/* Logo with Floating Animation */}
            <motion.div 
              className="absolute inset-0 flex items-center justify-center"
              animate={{
                y: [0, -10, 0],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            >
              <motion.div 
                className="bg-black/60 backdrop-blur-xl rounded-2xl p-8 md:p-10 border border-white/20 shadow-2xl"
                whileHover={{ scale: 1.05, rotate: [0, -5, 5, 0] }}
                transition={{ duration: 0.3 }}
              >
                <img 
                  src="/logo.png" 
                  alt="Alpha Foundry Logo" 
                  className="h-20 md:h-28 lg:h-36 w-auto drop-shadow-2xl"
                />
              </motion.div>
            </motion.div>
          </motion.div>

          {/* ETHOnline Badge */}
          <motion.div variants={fadeInUp} className="flex justify-center mb-6">
            <ShimmerCard className="inline-flex items-center gap-2 glass px-6 py-3 rounded-full border border-yellow-500/30">
              <motion.span 
                className="text-2xl"
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                🏆
              </motion.span>
              <span className="text-sm font-semibold bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
                ETHOnline 2025 Finalist
              </span>
            </ShimmerCard>
          </motion.div>

          {/* Title */}
          <motion.h1 
            variants={fadeInUp}
            className="text-5xl md:text-7xl font-heading font-bold gradient-text leading-tight"
          >
            Alpha Foundry
          </motion.h1>
          
          <motion.p 
            variants={fadeInUp}
            className="text-2xl md:text-3xl text-gray-300 font-light mb-4"
          >
            Encrypted DEX Intelligence Platform
          </motion.p>
          
          <motion.p 
            variants={fadeInUp}
            className="text-lg text-gray-400 max-w-3xl mx-auto leading-relaxed"
          >
            Real-time arbitrage opportunities secured by threshold cryptography. 
            Token-gated access to premium market data using decentralized encryption.
          </motion.p>

          {/* Tech Badges */}
          <motion.div 
            variants={staggerContainer}
            className="flex flex-wrap justify-center gap-3 mt-8"
          >
            {[
              { icon: "⚡", text: "Lighthouse Storage", color: "blue" },
              { icon: "🔍", text: "Blockscout MCP", color: "purple" },
              { icon: "/dexarb_image.png", text: "1MB.io DataCoin", color: "pink", isImage: true },
              { icon: "🤖", text: "ASI:One Ready", color: "green" }
            ].map((badge, i) => (
              <motion.span 
                key={i}
                variants={scaleIn}
                whileHover={{ scale: 1.1, y: -5 }}
                className="tech-badge flex items-center gap-2 cursor-pointer"
              >
                {badge.isImage ? (
                  <img src={badge.icon} alt="" className="w-5 h-5 rounded-full" />
                ) : (
                  <span className={`text-${badge.color}-400`}>{badge.icon}</span>
                )}
                <span className={`text-${badge.color}-400`}>💎</span> {badge.text}
              </motion.span>
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div 
            variants={staggerContainer}
            className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto mt-12"
          >
            {[
              { value: metadata?.rows?.toLocaleString() || '---', label: 'Swap Events Tracked' },
              { value: '100%', label: 'Encryption Coverage' },
              { value: metadata?.freshness_minutes !== undefined ? `${metadata.freshness_minutes}m` : '---', label: 'Data Freshness' }
            ].map((stat, i) => (
              <motion.div 
                key={i}
                variants={fadeInUp}
                whileHover={{ scale: 1.05, y: -5 }}
                className="card-highlight text-center cursor-pointer"
              >
                <ShimmerCard className="p-6">
                  <motion.div 
                    className="text-3xl font-bold gradient-text"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.5 + i * 0.1, type: "spring" }}
                  >
                    {stat.value}
                  </motion.div>
                  <div className="text-sm text-gray-400 mt-1">{stat.label}</div>
                </ShimmerCard>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* Wallet Section */}
        <motion.div
          ref={walletRef}
          initial="hidden"
          animate={walletInView ? "visible" : "hidden"}
          variants={staggerContainer}
          className="card-highlight mb-8"
        >
          <motion.div variants={fadeInUp} className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <motion.span 
                className="text-4xl"
                animate={{ rotate: [0, -10, 10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                🔐
              </motion.span>
              <h2 className="text-3xl font-heading font-bold">Wallet Connection</h2>
            </div>
            {!walletState.address ? (
              <MagneticButton
                onClick={connectWallet}
                disabled={isConnecting}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden group"
              >
                <span className="relative z-10">
                  {isConnecting ? (
                    <><motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} className="inline-block mr-2">⏳</motion.span> Connecting...</>
                  ) : (
                    <><span className="mr-2">🔌</span> Connect MetaMask</>
                  )}
                </span>
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600"
                  initial={{ x: "-100%" }}
                  whileHover={{ x: 0 }}
                  transition={{ duration: 0.3 }}
                />
              </MagneticButton>
            ) : (
              <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-right"
              >
                <div className="text-xs text-gray-400 mb-1">Connected Wallet</div>
                <div className="font-mono text-sm bg-white/5 px-3 py-1.5 rounded-lg">
                  {walletState.address.slice(0, 6)}...{walletState.address.slice(-4)}
                </div>
              </motion.div>
            )}
          </motion.div>

          {walletState.address && (
            <motion.div 
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-3 gap-4"
            >
              {/* Network Status */}
              <motion.div variants={slideInLeft} whileHover={{ scale: 1.02 }} className="stat-card">
                <div className="text-xs text-gray-400 mb-2 uppercase tracking-wide">Network</div>
                <div className="font-semibold">
                  {walletState.chainId === CHAIN_ID ? (
                    <span className="status-badge status-success">
                      <motion.span 
                        className="text-lg"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring" }}
                      >
                        ✓
                      </motion.span> {CHAIN_NAME}
                    </span>
                  ) : (
                    <span className="status-badge status-error">
                      <motion.span 
                        className="text-lg"
                        animate={{ rotate: [0, -10, 10, 0] }}
                        transition={{ duration: 0.5, repeat: Infinity }}
                      >
                        ✗
                      </motion.span> Wrong Network
                    </span>
                  )}
                </div>
              </motion.div>

              {/* Balance */}
              <motion.div variants={fadeInUp} whileHover={{ scale: 1.02 }} className="stat-card relative overflow-hidden">
                <div className="absolute top-0 right-0 opacity-5">
                  <motion.img 
                    src="/dexarb_image.png" 
                    alt="" 
                    className="w-24 h-24"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                  />
                </div>
                <div className="relative z-10">
                  <div className="text-xs text-gray-400 mb-2 uppercase tracking-wide flex items-center gap-2">
                    <img src="/dexarb_image.png" alt="DADC" className="w-4 h-4 rounded-full" />
                    DADC Balance
                  </div>
                  {walletState.balance && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 200 }}
                    >
                      <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                        {parseFloat(walletState.balance).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {Math.floor(parseFloat(walletState.balance))} decrypt{Math.floor(parseFloat(walletState.balance)) === 1 ? '' : 's'} remaining
                      </div>
                    </motion.div>
                  )}
                </div>
              </motion.div>

              {/* Access Status */}
              <motion.div variants={slideInRight} whileHover={{ scale: 1.02 }} className="stat-card">
                <div className="text-xs text-gray-400 mb-2 uppercase tracking-wide">Access Status</div>
                <div className="font-semibold">
                  {walletState.isEligible ? (
                    <span className="status-badge status-success">
                      <motion.span 
                        className="text-lg"
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1, repeat: Infinity }}
                      >
                        ✓
                      </motion.span> Access Granted
                    </span>
                  ) : (
                    <span className="status-badge status-warning">
                      <span className="text-lg">⚠</span> Needs Tokens
                    </span>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </motion.div>

        {/* Status Messages with Animation */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6"
            >
              <p className="text-red-300">{error}</p>
            </motion.div>
          )}
          
          {success && !error && (
            <motion.div
              initial={{ opacity: 0, y: -20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-green-900/50 border border-green-700 rounded-lg p-4 mb-6"
            >
              <p className="text-green-300">{success}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Rest of your content with similar animation patterns... */}
        {/* I'll add the complete implementation with all sections */}
      </div>

      {/* Floating Chat Button */}
      <motion.button
        className="fixed bottom-6 right-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-full p-4 shadow-lg z-50"
        whileHover={{ scale: 1.1, rotate: 5 }}
        whileTap={{ scale: 0.9 }}
        animate={{
          y: [0, -10, 0],
        }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </motion.button>
    </main>
  )
}
