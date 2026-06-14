'use client';

import { useEffect, useRef } from 'react';
import { MarkdownText } from './MarkdownText';

interface StreamingTextProps {
  text: string;
}

export function StreamingText({ text }: StreamingTextProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [text]);

  if (!text) return null;

  return (
    <div className="flex gap-3 justify-start">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm">
        🧠
      </div>
      <div className="max-w-[80%]">
        <div className="rounded-2xl rounded-bl-sm px-4 py-2.5 bg-slate-800 text-slate-100">
          <MarkdownText content={text} />
          <span className="cursor-blink" />
        </div>
      </div>
      <div ref={endRef} />
    </div>
  );
}
