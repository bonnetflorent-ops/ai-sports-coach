'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { User, levelLabel, WeeklySlot } from '@/types';
import { apiFetch } from '@/lib/api';
import { BugReport } from './BugReport';

// Noms lisibles pour les sports (valeur DB → affichage)
const SPORT_LABELS: Record<string, string> = {
  course_a_pied: 'Course à pied',
  cyclisme: 'Cyclisme',
  natation: 'Natation',
  triathlon: 'Triathlon',
  musculation: 'Musculation',
  trail: 'Trail',
  autre: 'Autre',
};

function sportLabel(value: string | undefined): string {
  if (!value) return 'Non renseigné';
  return SPORT_LABELS[value] || value;
}

export function ProfileView() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [bugReportOpen, setBugReportOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchProfile() {
      try {
        setLoading(true);
        const data = await apiFetch<User>('/api/profile');
        if (!cancelled) {
          setUser(data);
          // Mettre à jour localStorage pour les autres composants
          localStorage.setItem('user', JSON.stringify(data));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Impossible de charger le profil');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchProfile();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="space-y-4 p-4 max-w-2xl mx-auto w-full pb-24 md:pb-4">
        <div className="flex flex-col items-center gap-3 py-6">
          <Skeleton className="h-16 w-16 rounded-full bg-slate-800" />
          <Skeleton className="h-6 w-32 bg-slate-800" />
          <Skeleton className="h-4 w-48 bg-slate-800" />
        </div>
        <div className="rounded-xl bg-slate-900/50 border border-slate-800 p-4 space-y-3">
          <Skeleton className="h-5 w-40 bg-slate-800" />
          <Skeleton className="h-4 w-full bg-slate-800" />
          <Skeleton className="h-4 w-full bg-slate-800" />
          <Skeleton className="h-4 w-3/4 bg-slate-800" />
        </div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-4">
        <div className="text-center">
          <p className="text-4xl mb-4">👤</p>
          <p className="text-slate-400 text-lg">
            {error || 'Connecte-toi pour voir ton profil'}
          </p>
          {error && (
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Réessayer
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 max-w-2xl mx-auto w-full pb-24 md:pb-4">
      {/* Profile Header */}
      <div className="flex flex-col items-center gap-3 py-6">
        <div className="h-16 w-16 rounded-full bg-blue-600/20 flex items-center justify-center text-2xl font-bold text-blue-400">
          {user.first_name?.charAt(0)?.toUpperCase() || '👤'}
        </div>
        <h2 className="text-xl font-semibold text-slate-50">
          {user.first_name || 'Athlète'}
        </h2>
        {user.email && (
          <p className="text-sm text-slate-400">{user.email}</p>
        )}
      </div>

      {/* Sports Profile */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-slate-50 text-base">
            🏆 Mon profil sportif
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Sport</span>
            <span className="text-sm text-slate-50">
              {sportLabel(user.sport)}
            </span>
          </div>
          <Separator className="bg-slate-800" />
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Niveau</span>
            <span className="text-sm text-slate-50 font-medium">
              {levelLabel(user.level)}
            </span>
          </div>
          <Separator className="bg-slate-800" />
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Objectif</span>
            <span className="text-sm text-slate-50 max-w-[60%] text-right">
              {user.goal || 'Non renseigné'}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Weekly Slots */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-slate-50 text-base">
            📅 Mes dispos
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* weekly_slots peut être une string (DB) ou un tableau d'objets */}
          {user.weekly_slots ? (
            <div className="flex flex-wrap gap-2">
              {Array.isArray(user.weekly_slots) && user.weekly_slots.length > 0
                ? user.weekly_slots.map((slot, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {typeof slot === 'string' ? slot : `${(slot as WeeklySlot).day} ${(slot as WeeklySlot).time}`}
                    </Badge>
                  ))
                : <Badge variant="outline" className="text-xs">{String(user.weekly_slots)}</Badge>}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Aucun créneau renseigné</p>
          )}
        </CardContent>
      </Card>

      {/* Equipment */}
      {user.equipment && (
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-slate-50 text-base">
              🎒 Équipement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-300">
              {typeof user.equipment === 'string' ? user.equipment : JSON.stringify(user.equipment)}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="space-y-2">
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {}}
        >
          Modifier mon profil
        </Button>
      </div>

      {/* Bug Report */}
      <div className="pt-4 border-t border-slate-800">
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-slate-400 hover:text-slate-200"
          onClick={() => setBugReportOpen(true)}
        >
          Signaler un bug
        </Button>
      </div>

      <BugReport
        open={bugReportOpen}
        onClose={() => setBugReportOpen(false)}
      />
    </div>
  );
}
