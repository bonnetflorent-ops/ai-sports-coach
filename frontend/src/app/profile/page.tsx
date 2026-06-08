'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { BottomNav } from '@/components/layout/BottomNav';
import { ProfileView } from '@/components/profile/ProfileView';

export default function ProfilePage() {
  const router = useRouter();
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
      <Header />
      <TabNavigation />
      <main className="flex-1 overflow-y-auto">
        <ProfileView />
      </main>
      <BottomNav />
    </div>
  );
}
