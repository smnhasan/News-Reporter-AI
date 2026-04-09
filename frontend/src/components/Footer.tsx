'use client'

import React from 'react'
import Link from 'next/link'
import { MessageCircle, Twitter, Github, Linkedin, Mail } from 'lucide-react'

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
              <Link href="#" className="text-gray-500 hover:text-primary-400 transition-colors">
                <Twitter className="h-5 w-5" />
              </Link>
              <Link href="#" className="text-gray-500 hover:text-white transition-colors">
                <Github className="h-5 w-5" />
              </Link>
              <Link href="#" className="text-gray-500 hover:text-blue-400 transition-colors">
                <Linkedin className="h-5 w-5" />
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
