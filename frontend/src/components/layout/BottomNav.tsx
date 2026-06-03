'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const tabs = [
  { label: 'Chat', icon: '💬', href: '/' },
  { label: 'Dashboard', icon: '📊', href: '/dashboard' },
  { label: 'Profil', icon: '👤', href: '/profile' },
] as const;

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-slate-800 bg-slate-950/95 backdrop-blur">
      <div className="flex items-center justify-around h-16 max-w-2xl mx-auto">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex flex-col items-center gap-0.5 px-4 py-2 text-xs font-medium transition-colors ${
                isActive ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
