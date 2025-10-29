import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { Navigation } from './components/Navigation'
import { CommandPalette } from './components/CommandPalette'
import { FraudChatbot } from './components/FraudChatbot'

export const metadata: Metadata = {
  title: 'Fraud Detection Portal - AI-Powered Financial Crime Detection',
  description: 'Advanced fraud detection system with ML predictions, network analysis, and real-time monitoring',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet" />
      </head>
      <body className="font-inter">
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

