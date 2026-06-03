'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const tabs = [
  { label: 'Chat', icon: '💬', href: '/' },
  { label: 'Dashboard', icon: '📊', href: '/dashboard' },
  { label: 'Profil', icon: '👤', href: '/profile' },
] as const;

export function TabNavigation() {
  const pathname = usePathname();

  return (
    <nav className="hidden md:flex border-b border-slate-800">
      <div className="flex max-w-2xl mx-auto w-full">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                isActive
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
