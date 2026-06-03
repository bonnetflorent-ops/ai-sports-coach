'use client';

import { useState, useCallback, useRef } from 'react';
import { ChatMessage } from '@/types';
import { sseStream } from '@/lib/api';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [error, setError] = useState('');
  const controllerRef = useRef<AbortController | null>(null);
  const streamingTextRef = useRef('');

  const sendMessage = useCallback((content: string) => {
    setError('');

    const tempId = `temp-${Date.now()}`;
    const userMessage: ChatMessage = {
      id: tempId,
      session_id: '',
      user_id: '',
      role: 'user',
      content,
      tokens_used: 0,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setStreaming(true);
    setStreamingText('');
    streamingTextRef.current = '';

    const controller = sseStream(
      '/api/chat/message',
      { message: content },
      (token) => {
        streamingTextRef.current += token;
        setStreamingText(streamingTextRef.current);
      },
      (meta) => {
        const fullText = streamingTextRef.current;
        const assistantMessage: ChatMessage = {
          id: meta.message_id || `msg-${Date.now()}`,
          session_id: '',
          user_id: '',
          role: 'assistant',
          content: fullText,
          tokens_used: meta.tokens_used || 0,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setStreaming(false);
        setStreamingText('');
        streamingTextRef.current = '';
      },
      (err) => {
        setError(err.message);
        setStreaming(false);
        setStreamingText('');
        streamingTextRef.current = '';
      },
    );

    controllerRef.current = controller;
  }, []);

  const stopStreaming = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setStreaming(false);
    setStreamingText('');
    streamingTextRef.current = '';
  }, []);

  return { messages, streaming, streamingText, error, sendMessage, stopStreaming };
}
