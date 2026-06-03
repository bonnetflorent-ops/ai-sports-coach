'use client';

import { useState, useEffect } from 'react';
import { useDashboard } from '@/hooks/useDashboard';
import { apiFetch } from '@/lib/api';
import { UpcomingSession as UpcomingSessionType } from '@/types';
import { MetricCard } from './MetricCard';
import { LoadChart } from './LoadChart';
import { UpcomingSession } from './UpcomingSession';
import { AthleteKnowledge } from './AthleteKnowledge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

function DashboardSkeleton() {
  return (
    <div className="space-y-4 p-4 max-w-2xl mx-auto w-full">
      <div className="grid grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl bg-slate-900/50 border border-slate-800 p-4 space-y-3">
            <Skeleton className="h-4 w-20 bg-slate-800" />
            <Skeleton className="h-8 w-28 bg-slate-800" />
            <Skeleton className="h-3 w-12 bg-slate-800" />
          </div>
        ))}
      </div>
      <div className="rounded-xl bg-slate-900/50 border border-slate-800 p-4 space-y-3">
        <Skeleton className="h-5 w-48 bg-slate-800" />
        <Skeleton className="h-48 w-full bg-slate-800" />
      </div>
      <div className="rounded-xl bg-slate-900/50 border border-slate-800 p-4 space-y-3">
        <Skeleton className="h-5 w-36 bg-slate-800" />
        <Skeleton className="h-4 w-full bg-slate-800" />
      </div>
    </div>
  );
}

export function DashboardView() {
  const { metrics, chartData, loading, error } = useDashboard();
  const [upcomingSession, setUpcomingSession] = useState<UpcomingSessionType | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [period, setPeriod] = useState('30d');
  const [athleteModelOpen, setAthleteModelOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function fetchSession() {
      try {
        setSessionLoading(true);
        const data = await apiFetch<{ session: UpcomingSessionType | null }>(
          '/api/dashboard/upcoming'
        );
        if (!cancelled) {
          setUpcomingSession(data.session);
        }
      } catch {
        // Silently fail - session is optional
      } finally {
        if (!cancelled) setSessionLoading(false);
      }
    }
    fetchSession();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-4">
        <div className="text-center max-w-sm">
          <p className="text-4xl mb-4">😕</p>
          <p className="text-slate-400 text-lg mb-2">Impossible de charger le tableau de bord</p>
          <p className="text-sm text-red-400 mb-4">{error}</p>
          <Button
            variant="outline"
            onClick={() => window.location.reload()}
          >
            Réessayer
          </Button>
        </div>
      </div>
    );
  }

  if (metrics.length === 0 && !error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-4">
        <div className="text-center max-w-sm">
          <p className="text-4xl mb-4">📊</p>
          <p className="text-slate-400 text-lg mb-4">
            Ton coach n&apos;a pas encore assez de données. Continue à discuter avec lui !
          </p>
          <Button
            variant="outline"
            onClick={() => window.location.href = '/'}
          >
            Retour au chat
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 max-w-2xl mx-auto w-full pb-24 md:pb-4">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 gap-4">
        {metrics.map((m) => (
          <MetricCard
            key={m.name}
            name={m.name}
            value={m.value}
            unit={m.unit}
            trend={m.trend}
          />
        ))}
      </div>

      {/* Load Chart */}
      <LoadChart
        data={chartData}
        period={period}
        onPeriodChange={setPeriod}
      />

      {/* Upcoming Session */}
      {sessionLoading ? (
        <div className="rounded-xl bg-slate-900/50 border border-slate-800 p-4 space-y-3">
          <Skeleton className="h-5 w-36 bg-slate-800" />
          <Skeleton className="h-4 w-full bg-slate-800" />
        </div>
      ) : (
        <UpcomingSession session={upcomingSession} />
      )}

      {/* Athlete Model Button */}
      <div className="flex justify-center">
        <Button
          variant="ghost"
          className="text-slate-400 hover:text-slate-200"
          onClick={() => setAthleteModelOpen(true)}
        >
          Voir mon modèle athlète
        </Button>
      </div>

      {/* Athlete Knowledge Sheet */}
      <AthleteKnowledge
        open={athleteModelOpen}
        onClose={() => setAthleteModelOpen(false)}
      />
    </div>
  );
}
