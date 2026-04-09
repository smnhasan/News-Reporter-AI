'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ChatBox from '@/components/ChatBox'
import { useAuth } from '@/context/AuthContext'

export default function ChatPage() {
  const { token, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !token) {
      router.push('/login')
    }
  }, [token, loading, router])

  if (loading || !token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col overflow-hidden">
      {/* Chat Interface */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">
          <ChatBox />
        </div>
      </main>
    </div>
  )
}
