'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { User } from '@/types';
import { BugReport } from './BugReport';

export function ProfileView() {
  const [user] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [bugReportOpen, setBugReportOpen] = useState(false);

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] p-4">
        <div className="text-center">
          <p className="text-4xl mb-4">👤</p>
          <p className="text-slate-400 text-lg">
            Connecte-toi pour voir ton profil
          </p>
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
            <div className="flex gap-1">
              {(user.sports || []).map((sport, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {sport}
                </Badge>
              ))}
              {(!user.sports || user.sports.length === 0) && (
                <span className="text-sm text-slate-500">Non renseigné</span>
              )}
            </div>
          </div>
          <Separator className="bg-slate-800" />
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Niveau</span>
            <span className="text-sm text-slate-50 font-medium capitalize">
              {user.level || 'Non renseigné'}
            </span>
          </div>
          <Separator className="bg-slate-800" />
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">Objectifs</span>
            <span className="text-sm text-slate-50 max-w-[60%] text-right">
              {user.goals && typeof user.goals === 'object' && Object.keys(user.goals).length > 0
                ? JSON.stringify(user.goals)
                : 'Non renseigné'}
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
          {user.weekly_slots && user.weekly_slots.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {user.weekly_slots.map((slot, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {slot.day} {slot.time}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">Aucun créneau renseigné</p>
          )}
        </CardContent>
      </Card>

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
