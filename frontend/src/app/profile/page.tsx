'use client';

import { Header } from '@/components/layout/Header';
import { TabNavigation } from '@/components/layout/TabNavigation';
import { BottomNav } from '@/components/layout/BottomNav';

export default function ProfilePage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <TabNavigation />
      <main className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-4xl mb-4">👤</p>
          <p className="text-slate-400 text-lg">Profil — bientôt disponible</p>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
