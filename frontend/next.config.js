/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow your domain for HMR (Hot Module Replacement) in development
  allowedDevOrigins: ['chatbot.test.nascenia.com'],

  // Keep your API rewrites (this is useful for development)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',   // Fixed: removed extra /api
      },
    ]
  },

  // Optional but recommended improvements
  reactStrictMode: true,
}

module.exports = nextConfig