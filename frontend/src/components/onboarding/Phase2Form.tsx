'use client';

import { useState, FormEvent } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiFetch } from '@/lib/api';

interface Phase2FormProps {
  onSuccess: () => void;
  onSkip: () => void;
}

export function Phase2Form({ onSuccess, onSkip }: Phase2FormProps) {
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    const body: Record<string, string | number> = {};
    if (weight) body.weight_kg = parseFloat(weight);
    if (height) body.height_cm = parseFloat(height);
    if (age) body.age = parseInt(age, 10);
    if (gender) body.gender = gender;
    if (email) body.email = email.trim();

    setLoading(true);
    try {
      await apiFetch('/api/onboarding/phase2', {
        method: 'POST',
        body: JSON.stringify(body),
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
        <Label htmlFor="weight">Poids (kg)</Label>
        <Input
          id="weight"
          type="number"
          step="0.1"
          min="0"
          placeholder="Ex: 70"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="height">Taille (cm)</Label>
        <Input
          id="height"
          type="number"
          step="1"
          min="0"
          placeholder="Ex: 175"
          value={height}
          onChange={(e) => setHeight(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="age">Âge</Label>
        <Input
          id="age"
          type="number"
          step="1"
          min="0"
          placeholder="Ex: 30"
          value={age}
          onChange={(e) => setAge(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="gender">Genre</Label>
        <Select value={gender} onValueChange={(v) => v && setGender(v)}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Non spécifié" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="homme">Homme</SelectItem>
            <SelectItem value="femme">Femme</SelectItem>
            <SelectItem value="autre">Autre</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email de contact</Label>
        <Input
          id="email"
          type="email"
          placeholder="vous@exemple.fr"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex gap-3">
        <Button
          type="button"
          variant="outline"
          className="flex-1"
          onClick={onSkip}
        >
          Passer
        </Button>
        <Button type="submit" className="flex-1" disabled={loading}>
          {loading ? 'Enregistrement...' : 'Continuer'}
        </Button>
      </div>
    </form>
  );
}
