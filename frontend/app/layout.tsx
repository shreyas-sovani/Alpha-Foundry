import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DEXArb Data Unlock | ETHOnline 2025',
  description: 'Token-gated access to encrypted DEX arbitrage data. Connect wallet, claim DADC tokens, and decrypt real-time swap feeds from Lighthouse Storage.',
  keywords: ['DEX', 'Arbitrage', 'MEV', 'Lighthouse', 'DataCoin', 'ETHOnline', 'Encrypted Data'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
