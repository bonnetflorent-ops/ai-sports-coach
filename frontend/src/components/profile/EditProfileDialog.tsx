'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { User, levelLabel } from '@/types';
import { apiFetch } from '@/lib/api';

interface EditProfileDialogProps {
  open: boolean;
  onClose: () => void;
  user: User;
  onSaved: (updated: User) => void;
}

const SPORT_OPTIONS = [
  { value: 'course_a_pied', label: 'Course à pied' },
  { value: 'cyclisme', label: 'Cyclisme' },
  { value: 'natation', label: 'Natation' },
  { value: 'triathlon', label: 'Triathlon' },
  { value: 'trail', label: 'Trail' },
  { value: 'musculation', label: 'Musculation' },
  { value: 'autre', label: 'Autre' },
];

const LEVEL_OPTIONS = [
  { value: 1, label: 'Débutant' },
  { value: 2, label: 'Intermédiaire' },
  { value: 3, label: 'Avancé' },
];

export function EditProfileDialog({ open, onClose, user, onSaved }: EditProfileDialogProps) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');
    setSaving(true);

    const form = new FormData(e.currentTarget);

    // Construire les mises à jour (seulement les champs modifiés)
    const updates: Record<string, unknown> = {};

    const firstName = form.get('first_name') as string;
    if (firstName && firstName !== user.first_name) updates.first_name = firstName;

    const sport = form.get('sport') as string;
    if (sport !== user.sport) updates.sports = sport; // le mapping backend gère sports→sport

    const level = parseInt(form.get('level') as string);
    if (level !== user.level) updates.level = level;

    const goal = form.get('goal') as string;
    if (goal !== (user.goal || '')) updates.goals = goal; // le mapping backend gère goals→goal

    const weight = form.get('weight_kg') as string;
    if (weight) {
      const w = parseFloat(weight);
      if (w !== user.weight_kg) updates.weight_kg = w;
    }

    const height = form.get('height_cm') as string;
    if (height) {
      const h = parseFloat(height);
      if (h !== user.height_cm) updates.height_cm = h;
    }

    const age = form.get('age') as string;
    if (age) {
      const a = parseInt(age);
      if (a !== user.age) updates.age = a;
    }

    const gender = form.get('gender') as string;
    if (gender && gender !== (user.gender || '')) updates.gender = gender;

    if (Object.keys(updates).length === 0) {
      onClose();
      setSaving(false);
      return;
    }

    try {
      const updated = await apiFetch<User>('/api/profile', {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
      localStorage.setItem('user', JSON.stringify(updated));
      onSaved(updated);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Modifier mon profil</DialogTitle>
          <DialogDescription>
            Modifie les informations ci-dessous puis enregistre.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Prénom */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Prénom</label>
            <input
              name="first_name"
              defaultValue={user.first_name || ''}
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            />
          </div>

          {/* Sport */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Sport</label>
            <select
              name="sport"
              defaultValue={user.sport || ''}
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            >
              <option value="">-- Choisir --</option>
              {SPORT_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          {/* Niveau */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">
              Niveau ({levelLabel(user.level)})
            </label>
            <select
              name="level"
              defaultValue={user.level || 1}
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            >
              {LEVEL_OPTIONS.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
          </div>

          {/* Objectif */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Objectif</label>
            <input
              name="goal"
              defaultValue={user.goal || ''}
              placeholder="Ex: terminer un semi-marathon"
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            />
          </div>

          <hr className="border-slate-800" />
          <p className="text-xs text-slate-500 font-medium">Données physiologiques</p>

          {/* Poids (kg) */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Poids (kg)</label>
            <input
              name="weight_kg"
              type="number"
              step="0.1"
              min="30"
              max="250"
              defaultValue={user.weight_kg ?? ''}
              placeholder="Ex: 70"
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            />
          </div>

          {/* Taille (cm) */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Taille (cm)</label>
            <input
              name="height_cm"
              type="number"
              step="0.1"
              min="100"
              max="250"
              defaultValue={user.height_cm ?? ''}
              placeholder="Ex: 175"
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            />
          </div>

          {/* Âge */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Âge</label>
            <input
              name="age"
              type="number"
              min="10"
              max="120"
              defaultValue={user.age ?? ''}
              placeholder="Ex: 30"
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            />
          </div>

          {/* Genre */}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Genre</label>
            <select
              name="gender"
              defaultValue={user.gender || ''}
              className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            >
              <option value="">-- Non renseigné --</option>
              <option value="homme">Homme</option>
              <option value="femme">Femme</option>
              <option value="autre">Autre</option>
            </select>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/50 px-3 py-2 rounded-lg">{error}</p>
          )}

          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
              Annuler
            </Button>
            <Button type="submit" className="flex-1" disabled={saving}>
              {saving ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
