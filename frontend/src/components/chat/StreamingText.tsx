'use client';

import { useEffect, useRef, useState } from 'react';

interface StreamingTextProps {
  text: string;
}

export function StreamingText({ text }: StreamingTextProps) {
  const [visible, setVisible] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible((v) => !v);
    }, 530);
    return () => clearInterval(interval);
  }, []);

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
          <p className="text-sm whitespace-pre-wrap">
            {text}
            <span
              className={`inline-block w-[2px] h-[1em] ml-0.5 align-middle bg-slate-100 transition-opacity ${
                visible ? 'opacity-100' : 'opacity-0'
              }`}
            />
          </p>
        </div>
      </div>
      <div ref={endRef} />
    </div>
  );
}
