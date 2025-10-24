import type { Metadata } from 'next'
import { Space_Grotesk, Inter } from 'next/font/google'
import './globals.css'

const spaceGrotesk = Space_Grotesk({ 
  subsets: ['latin'],
  variable: '--font-space-grotesk',
  display: 'swap',
})

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Alpha Foundry | ETHOnline 2025',
  description: 'Token-gated encrypted DEX intelligence platform. Real-time arbitrage data secured by Lighthouse, powered by Blockscout MCP, 1MB.io, and ASI:One.',
  keywords: ['ETHOnline 2025', 'Lighthouse', 'Blockscout MCP', '1MB.io', 'ASI:One', 'DEX', 'Arbitrage', 'MEV', 'DataCoin', 'Encrypted Data', 'Token-Gating'],
  openGraph: {
    title: 'Alpha Foundry - Encrypted DEX Intelligence',
    description: 'Token-gated access to real-time arbitrage opportunities. Built for ETHOnline 2025.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${inter.variable}`}>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
