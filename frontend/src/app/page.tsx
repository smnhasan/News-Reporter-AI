import Link from 'next/link'
import { Brain, Zap, Shield, MessageCircle } from 'lucide-react'
export default function ChatPage() {
  return (
    <div className="bg-gradient-to-br from-primary-50 to-white">

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6">
            Verify News Instantly
            <span className="text-primary-600 block">Powered by AI</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            News Reporter AI verifies rumors and delivers accurate, up-to-date information from credible 
            news sources, ensuring you stay informed with reliable answers.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/chat" className="btn-primary inline-flex items-center text-lg px-8 py-3">
              <MessageCircle className="mr-2 h-5 w-5" />
              Start Chatting
            </Link>
            <Link href="/about" className="btn-secondary inline-flex items-center text-lg px-8 py-3">
              Learn More
            </Link>
          </div>
        </div>

        {/* Features */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="bg-primary-100 rounded-full p-4 w-16 h-16 mx-auto mb-4">
              <Brain className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Smart Verification</h3>
            <p className="text-gray-600">
              Advanced algorithms verify news and rumors using credible sources for accurate responses.
            </p>
          </div>
          <div className="text-center p-6">
            <div className="bg-primary-100 rounded-full p-4 w-16 h-16 mx-auto mb-4">
              <Zap className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Lightning Fast</h3>
            <p className="text-gray-600">
              Instant answers powered by optimized retrieval and processing systems.
            </p>
          </div>
          <div className="text-center p-6">
            <div className="bg-primary-100 rounded-full p-4 w-16 h-16 mx-auto mb-4">
              <Shield className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Reliable & Safe</h3>
            <p className="text-gray-600">
              Designed with security and reliability to keep your queries private and trustworthy.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <MessageCircle className="h-6 w-6" />
              <span className="text-lg font-semibold">News Reporter AI</span>
            </div>
            <p className="text-gray-400">
              Powered by advanced AI for reliable news verification and updates.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
