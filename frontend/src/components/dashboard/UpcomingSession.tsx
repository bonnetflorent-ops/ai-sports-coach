'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { UpcomingSession as UpcomingSessionType } from '@/types';

interface UpcomingSessionProps {
  session: UpcomingSessionType | null;
}

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr);
  return d.toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });
};

export function UpcomingSession({ session }: UpcomingSessionProps) {
  if (!session) {
    return (
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="p-6 text-center">
          <p className="text-slate-400 text-sm mb-3">
            Pas de séance planifiée. Demande à ton coach !
          </p>
          <Link href="/">
            <Button variant="outline" size="sm">
              Discuter avec mon coach
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardHeader>
        <CardTitle className="text-slate-50 text-base flex items-center gap-2">
          <span>🏋️</span>
          <span>Prochaine séance</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Date</span>
          <span className="text-sm text-slate-50 font-medium">
            {formatDate(session.date)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Type</span>
          <span className="text-sm text-blue-400 font-medium capitalize">
            {session.type}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Durée</span>
          <span className="text-sm text-slate-50 font-medium">
            {session.duration}
          </span>
        </div>
        {session.description && (
          <div className="pt-2 border-t border-slate-800">
            <p className="text-sm text-slate-300">{session.description}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
