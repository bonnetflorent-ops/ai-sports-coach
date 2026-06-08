'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { BottomNav } from '@/components/layout/BottomNav';
import { ChatView } from '@/components/chat/ChatView';

export default function HomePage() {
  const router = useRouter();
  const [badgeCount, setBadgeCount] = useState(0);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.replace('/auth/login');
    } else {
      setReady(true);
    }
  }, [router]);

  if (!ready) return null;

  return (
    <div className="flex flex-col min-h-screen">
      <Header badgeCount={badgeCount} />
      <TabNavigation />
      <main className="flex-1 overflow-hidden">
        <ChatView />
      </main>
      <BottomNav />
    </div>
  );
}
