'use client'

import React from 'react'
import { User, Bot } from 'lucide-react'
import clsx from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
interface MessageBubbleProps {
  message: string
  isBot: boolean
  timestamp: Date
}

export default function MessageBubble({ message, isBot, timestamp }: MessageBubbleProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className={clsx(
      'flex max-w-4xl w-full',
      isBot ? 'justify-start' : 'justify-end'
    )}>
      {/* Avatar */}
      <div className={clsx(
        'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1',
        isBot ? 'bg-blue-100 text-blue-600' : 'bg-gray-700 text-white'
      )}>
        {isBot ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
      </div>

      {/* Message Content */}
      <div className={clsx(
        'flex flex-col max-w-[80%]',
        isBot ? 'items-start' : 'items-end'
      )}>
        <div className={clsx(
          'message-bubble rounded-lg px-4 py-2',
          isBot 
            ? 'bg-blue-50 text-gray-900 ml-2' 
            : 'bg-gray-700 text-white ml-2'
        )}>
          {isBot ? (
            <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-gray-800 prose-pre:text-gray-100">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message}
            </p>
          )}
        </div>
        
        {/* Timestamp */}
        <span className="text-xs text-gray-400 mt-1 px-2" suppressHydrationWarning>
          {formatTime(timestamp)}
        </span>
      </div>
    </div>
  )
}
