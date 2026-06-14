'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { BottomNav } from '@/components/layout/BottomNav';
import { ProfileView } from '@/components/profile/ProfileView';
import { FactsDialog } from '@/components/chat/FactsDialog';
import { apiFetch } from '@/lib/api';

export default function ProfilePage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [badgeCount, setBadgeCount] = useState(0);
  const [factsOpen, setFactsOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.replace('/auth/login');
    } else {
      setReady(true);
    }
  }, [router]);

  useEffect(() => {
    if (!ready) return;
    apiFetch<{ facts: unknown[]; total: number }>('/api/facts')
      .then((data) => setBadgeCount(data.total))
      .catch(() => {});
  }, [ready]);

  if (!ready) return null;

  return (
    <div className="flex flex-col min-h-screen">
      <Header badgeCount={badgeCount} onBadgeClick={() => setFactsOpen(true)} />
      <TabNavigation />
      <main className="flex-1 overflow-y-auto">
        <ProfileView />
      </main>
      <BottomNav />
      <FactsDialog open={factsOpen} onClose={() => setFactsOpen(false)} />
    </div>
  );
}
