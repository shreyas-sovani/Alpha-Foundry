/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    // Backend metadata endpoint (Railway)
    NEXT_PUBLIC_METADATA_API: process.env.NEXT_PUBLIC_METADATA_API || 'http://localhost:8787',
    
    // Sepolia Testnet Configuration
    NEXT_PUBLIC_CHAIN_ID: '11155111',
    NEXT_PUBLIC_CHAIN_NAME: 'Sepolia',
    NEXT_PUBLIC_RPC_URL: 'https://ethereum-sepolia-rpc.publicnode.com',
    
    // DataCoin Contract (deployed on Sepolia)
    NEXT_PUBLIC_DATACOIN_ADDRESS: '0x8d302FfB73134235EBaD1B9Cd9C202d14f906FeC',
    
    // Faucet Contract (for claiming tokens)
    NEXT_PUBLIC_FAUCET_ADDRESS: '0xB0864079e5A5f898Da37ffF6c8bce762A2eD35BB',
    
    // Minimum DADC balance required for access
    NEXT_PUBLIC_MIN_BALANCE: '1.0',
  },
}

module.exports = nextConfig
