'use client'

import React from 'react'
import Link from 'next/link'
import { MessageCircle, X, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-900 border-t border-gray-800 pt-12 pb-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand Column */}
          <div className="col-span-1 md:col-span-1">
            <Link href="/" className="flex items-center space-x-2 mb-4">
              <MessageCircle className="h-8 w-8 text-primary-400" />
              <span className="text-xl font-bold text-white">News Reporter AI</span>
            </Link>
            <p className="text-gray-400 text-sm leading-relaxed">
              Powered by advanced AI for reliable news verification and updates. Providing accuracy in the age of information.
            </p>
          </div>

          {/* Quick Links */}
          <div className="col-span-1">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Platform</h3>
            <ul className="space-y-3">
              <li>
                <Link href="/chat" className="text-gray-400 hover:text-primary-400 text-sm transition-colors">Chat Now</Link>
              </li>
              <li>
                <Link href="/about" className="text-gray-400 hover:text-primary-400 text-sm transition-colors">About Project</Link>
              </li>
              <li>
                <Link href="/login" className="text-gray-400 hover:text-primary-400 text-sm transition-colors">Sign In</Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div className="col-span-1">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Support</h3>
            <ul className="space-y-3">
              <li>
                <Link href="#" className="text-gray-400 hover:text-primary-400 text-sm transition-colors">Terms of Service</Link>
              </li>
              <li>
                <Link href="#" className="text-gray-400 hover:text-primary-400 text-sm transition-colors">Privacy Policy</Link>
              </li>
              <li>
                <Link href="mailto:support@newsreporter.ai" className="text-gray-400 hover:text-primary-400 text-sm transition-colors flex items-center">
                  <Mail className="h-4 w-4 mr-2" />
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Social */}
          <div className="col-span-1">
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Follow Us</h3>
            <div className="flex space-x-5">
              {/* X (formerly Twitter) */}
              <Link href="#" className="text-gray-500 hover:text-primary-400 transition-colors">
                <X className="h-5 w-5" />
              </Link>

              {/* GitHub SVG */}
              <Link href="#" className="text-gray-500 hover:text-white transition-colors">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="h-5 w-5"
                  aria-label="GitHub"
                >
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.418-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23a11.52 11.52 0 0 1 3-.405c1.02.005 2.045.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.605-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 21.795 24 17.295 24 12c0-6.63-5.37-12-12-12z" />
                </svg>
              </Link>

              {/* LinkedIn SVG */}
              <Link href="#" className="text-gray-500 hover:text-blue-400 transition-colors">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="h-5 w-5"
                  aria-label="LinkedIn"
                >
                  <path d="M20.447 20.452H16.89v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a1.977 1.977 0 1 1 0-3.953 1.977 1.977 0 0 1 0 3.953zm1.958 13.019H3.379V9h3.916v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </Link>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-500 text-sm mb-4 md:mb-0" suppressHydrationWarning>
            &copy; {new Date().getFullYear()} News Reporter AI. All rights reserved.
          </p>
          <div className="flex space-x-6 text-sm text-gray-500">
            <span>Powered by advanced AI for reliable news verification and updates.</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
