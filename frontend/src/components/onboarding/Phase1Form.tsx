'use client';

import { useState, FormEvent } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiFetch } from '@/lib/api';

interface Phase1FormProps {
  onSuccess: () => void;
}

const sports = [
  { value: 'cyclisme', label: 'Cyclisme' },
  { value: 'course_a_pied', label: 'Course à pied' },
  { value: 'natation', label: 'Natation' },
  { value: 'triathlon', label: 'Triathlon' },
  { value: 'musculation', label: 'Musculation' },
  { value: 'autre', label: 'Autre' },
];

const levels = [
  { value: 'debutant', label: 'Débutant' },
  { value: 'intermediaire', label: 'Intermédiaire' },
  { value: 'avance', label: 'Avancé' },
];

export function Phase1Form({ onSuccess }: Phase1FormProps) {
  const [sport, setSport] = useState('');
  const [level, setLevel] = useState('');
  const [goal, setGoal] = useState('');
  const [injuries, setInjuries] = useState('');
  const [equipment, setEquipment] = useState('');
  const [slots, setSlots] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (!sport || !level || !goal || !injuries || !slots) {
      setError('Veuillez remplir tous les champs obligatoires');
      return;
    }

    setLoading(true);
    try {
      await apiFetch('/api/onboarding/phase1', {
        method: 'POST',
        body: JSON.stringify({
          sport,
          level,
          goal,
          injuries,
          equipment: equipment || '',
          slots,
        }),
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="sport">
          Sport principal <span className="text-red-400">*</span>
        </Label>
        <Select value={sport} onValueChange={(v) => v && setSport(v)}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Choisis ton sport" />
          </SelectTrigger>
          <SelectContent>
            {sports.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="level">
          Niveau <span className="text-red-400">*</span>
        </Label>
        <Select value={level} onValueChange={(v) => v && setLevel(v)}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Choisis ton niveau" />
          </SelectTrigger>
          <SelectContent>
            {levels.map((l) => (
              <SelectItem key={l.value} value={l.value}>
                {l.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="goal">
          Objectif principal <span className="text-red-400">*</span>
        </Label>
        <Textarea
          id="goal"
          placeholder="Ex: Préparer un marathon en 4h, perdre 5kg, améliorer mon FTP..."
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="injuries">
          Blessures ou limitations <span className="text-red-400">*</span>
        </Label>
        <Textarea
          id="injuries"
          placeholder="Ex: Tendinite rotulienne, lombalgie chronique..."
          value={injuries}
          onChange={(e) => setInjuries(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="equipment">Équipement disponible</Label>
        <Textarea
          id="equipment"
          placeholder="Ex: Vélo de route, home trainer, tapis de course, haltères... (optionnel)"
          value={equipment}
          onChange={(e) => setEquipment(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="slots">
          Créneaux hebdomadaires <span className="text-red-400">*</span>
        </Label>
        <Input
          id="slots"
          placeholder="Lun 18h, Mer 7h, Sam 9h"
          value={slots}
          onChange={(e) => setSlots(e.target.value)}
          required
        />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Enregistrement...' : 'Continuer'}
      </Button>
    </form>
  );
}
