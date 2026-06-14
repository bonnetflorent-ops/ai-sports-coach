'use client';

import { useEffect, useRef } from 'react';
import { useChat } from '@/hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { StreamingText } from './StreamingText';
import { MessageInput } from './MessageInput';

export function ChatView() {
  const { messages, streaming, streamingText, error, loadingHistory, sendMessage, stopStreaming } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 max-w-2xl mx-auto w-full">
        {loadingHistory && messages.length === 0 && (
          <div className="flex items-center justify-center h-full min-h-[60vh]">
            <p className="text-slate-500 text-sm animate-pulse">Chargement de la conversation...</p>
          </div>
        )}
        {!loadingHistory && messages.length === 0 && !streaming && (
          <div className="flex items-center justify-center h-full min-h-[60vh]">
            <div className="text-center">
              <p className="text-4xl mb-4">👋</p>
              <p className="text-slate-400 text-lg">
                Dis bonjour à ton coach !
              </p>
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {streaming && <StreamingText text={streamingText} />}
        {error && (
          <div className="flex flex-col items-center gap-2">
            <p className="text-sm text-red-400 bg-red-950/50 px-4 py-2 rounded-lg">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-xs text-slate-400 hover:text-slate-200 underline"
            >
              Réessayer
            </button>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <MessageInput onSend={sendMessage} disabled={streaming} />
    </div>
  );
}
