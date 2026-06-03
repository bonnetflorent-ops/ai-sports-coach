'use client';

import { Header } from '@/components/layout/Header';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { BottomNav } from '@/components/layout/BottomNav';
import { ProfileView } from '@/components/profile/ProfileView';

export default function ProfilePage() {
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
