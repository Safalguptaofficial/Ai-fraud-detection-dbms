/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true, // Required for static export
  },
  // GitHub Pages deploys to a subdirectory
  basePath: process.env.NODE_ENV === 'production' ? '/Ai-fraud-detection-dbms' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/Ai-fraud-detection-dbms/' : '',
}

module.exports = nextConfig

