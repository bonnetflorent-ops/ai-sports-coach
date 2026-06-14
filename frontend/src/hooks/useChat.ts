'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { ChatMessage } from '@/types';
import { sseStream, apiFetch } from '@/lib/api';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [error, setError] = useState('');
  const [loadingHistory, setLoadingHistory] = useState(true);
  const controllerRef = useRef<AbortController | null>(null);
  const streamingTextRef = useRef('');
  const historyLoadedRef = useRef(false);

  // Charger l'historique des derniers messages au montage
  useEffect(() => {
    if (historyLoadedRef.current) return;
    historyLoadedRef.current = true;

    async function loadHistory() {
      try {
        const data = await apiFetch<{
          messages: Array<{
            id: string;
            role: 'user' | 'assistant';
            content: string;
            created_at: string;
            session_id: string;
          }>;
        }>('/api/chat/history?page=1&per_page=20');

        if (data.messages && data.messages.length > 0) {
          // L'API retourne déjà les messages en ordre chronologique (get_user_messages_paginated
          // fait un reversed() sur les résultats DESC)
          const historyMessages: ChatMessage[] = data.messages
            .map((msg) => ({
              id: msg.id,
              session_id: msg.session_id || '',
              user_id: '',
              role: msg.role,
              content: msg.content,
              tokens_used: 0,
              created_at: msg.created_at,
            }));
          setMessages(historyMessages);
        }
      } catch (err) {
        // Silencieux : l'historique est un bonus, pas un bloquant
        console.warn('Impossible de charger l\'historique:', err);
      } finally {
        setLoadingHistory(false);
      }
    }

    loadHistory();
  }, []);

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

  return { messages, streaming, streamingText, error, loadingHistory, sendMessage, stopStreaming };
}
