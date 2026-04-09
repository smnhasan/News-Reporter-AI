'use client'

import React from 'react'
import Link from 'next/link'
import { MessageCircle, LogOut, User as UserIcon } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

export default function Header() {
  const { token, logout } = useAuth()

  return (
    <header className="py-6 px-4 sm:px-6 lg:px-8 bg-white border-b border-gray-100">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <Link href="/" className="flex items-center space-x-2">
          <MessageCircle className="h-8 w-8 text-primary-600" />
          <h1 className="text-2xl font-bold text-gray-900">News Reporter AI</h1>
        </Link>
        <nav className="flex items-center space-x-6">
          <Link href="/chat" className="text-gray-600 hover:text-primary-600 transition-colors font-medium">
            Chat
          </Link>
          <Link href="/about" className="text-gray-600 hover:text-primary-600 transition-colors font-medium">
            About
          </Link>
          
          {token ? (
            <div className="flex items-center space-x-4 ml-4 pl-4 border-l border-gray-200">
              <button 
                onClick={logout}
                className="flex items-center space-x-1 text-gray-600 hover:text-red-600 transition-colors font-medium"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-4 ml-4 pl-4 border-l border-gray-200">
              <Link href="/login" className="text-gray-600 hover:text-primary-600 transition-colors font-medium">
                Log in
              </Link>
              <Link href="/register" className="btn-primary px-4 py-2 text-sm">
                Get Started
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  )
}
