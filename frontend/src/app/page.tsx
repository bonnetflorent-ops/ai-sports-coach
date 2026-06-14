'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { BottomNav } from '@/components/layout/BottomNav';
import { ChatView } from '@/components/chat/ChatView';
import { FactsDialog } from '@/components/chat/FactsDialog';
import { PwaInstallBanner } from '@/components/layout/PwaInstallBanner';
import { apiFetch } from '@/lib/api';

export default function HomePage() {
  const router = useRouter();
  const [badgeCount, setBadgeCount] = useState(0);
  const [factsOpen, setFactsOpen] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.replace('/auth/login');
    } else {
      setReady(true);
    }
  }, [router]);

  // Charger le nombre de faits
  useEffect(() => {
    if (!ready) return;

    async function fetchFactsCount() {
      try {
        const data = await apiFetch<{ facts: unknown[]; total: number }>('/api/facts');
        setBadgeCount(data.total);
      } catch {
        // Silencieux — le bouton affichera 0
      }
    }

    fetchFactsCount();
  }, [ready]);

  if (!ready) return null;

  return (
    <div className="flex flex-col min-h-screen">
      <Header
        badgeCount={badgeCount}
        onBadgeClick={() => setFactsOpen(true)}
      />
      <TabNavigation />
      <main className="flex-1 overflow-hidden">
        <ChatView />
      </main>
      <BottomNav />
      <PwaInstallBanner />

      <FactsDialog
        open={factsOpen}
        onClose={() => setFactsOpen(false)}
      />
    </div>
  );
}
