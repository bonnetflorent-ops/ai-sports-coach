'use client';

import { useEffect, useState } from 'react';
import { Brain } from 'lucide-react';

interface HeaderProps {
  badgeCount?: number;
  onBadgeClick?: () => void;
}

export function Header({ badgeCount = 0, onBadgeClick }: HeaderProps) {
  const [userName, setUserName] = useState('');
  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      const user = JSON.parse(stored);
      setUserName(user.first_name || 'Athlète');
    }
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
      <div className="flex items-center justify-between px-4 h-14 max-w-2xl mx-auto">
        <div>
          <h1 className="text-lg font-semibold">💬 Ton coach</h1>
          <p className="text-xs text-emerald-400">● en ligne</p>
        </div>
        <button
          onClick={onBadgeClick}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-800 hover:bg-slate-700 transition-colors"
        >
          <Brain className="w-4 h-4 text-amber-400" />
          <span className="text-sm font-medium">{badgeCount} faits</span>
        </button>
      </div>
    </header>
  );
}
