import { ChatMessage } from '@/types';
import { FeedbackButtons } from './FeedbackButtons';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm">
          🧠
        </div>
      )}
      <div className="max-w-[80%] space-y-1">
        <div
          className={`rounded-2xl px-4 py-2.5 ${
            isUser
              ? 'bg-blue-600 text-white rounded-br-sm'
              : 'bg-slate-800 text-slate-100 rounded-bl-sm'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        {!isUser && <FeedbackButtons messageId={message.id} />}
      </div>
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm">
          👤
        </div>
      )}
    </div>
  );
}
