'use client';

import { useState } from 'react';
import { apiFetch } from '@/lib/api';

interface FeedbackButtonsProps {
  messageId: string;
}

const dislikeOptions = [
  'Pas pertinent',
  'Trop long',
  'Erreur factuelle',
  'Autre',
] as const;

export function FeedbackButtons({ messageId }: FeedbackButtonsProps) {
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  async function sendFeedback(type: 'like' | 'dislike', detail?: string) {
    try {
      await apiFetch('/api/chat/feedback', {
        method: 'POST',
        body: JSON.stringify({ message_id: messageId, type, detail }),
      });
      setFeedbackSent(true);
      setShowMenu(false);
      setTimeout(() => setFeedbackSent(false), 3000);
    } catch {
      // silently fail
    }
  }

  function handleDislikeSelect(option: string) {
    sendFeedback('dislike', option);
  }

  if (feedbackSent) {
    return (
      <div className="flex items-center gap-2 mt-1 ml-1">
        <span className="text-xs text-emerald-400">Merci !</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-1 ml-1 relative">
      <button
        onClick={() => sendFeedback('like')}
        className="text-xs text-slate-500 hover:text-emerald-400 transition-colors p-1"
        title="Utile"
        data-testid="feedback-like"
      >
        👍
      </button>
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="text-xs text-slate-500 hover:text-red-400 transition-colors p-1"
        title="Pas utile"
      >
        👎
      </button>
      {showMenu && (
        <div className="absolute bottom-6 left-0 bg-slate-800 border border-slate-700 rounded-lg shadow-lg py-1 z-10">
          {dislikeOptions.map((option) => (
            <button
              key={option}
              onClick={() => handleDislikeSelect(option)}
              className="block w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 whitespace-nowrap"
            >
              {option}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
