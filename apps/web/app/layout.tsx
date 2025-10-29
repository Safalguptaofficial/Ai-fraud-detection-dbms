import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from './components/Navigation'
import { CommandPalette } from './components/CommandPalette'
import { FraudChatbot } from './components/FraudChatbot'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Fraud Detection Portal',
  description: 'AI-Powered Fraud Detection & Financial Crime',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <Navigation />
          <CommandPalette />
          <FraudChatbot />
          {children}
        </Providers>
      </body>
    </html>
  )
}

