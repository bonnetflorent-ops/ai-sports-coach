'use client';

import { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { apiFetch } from '@/lib/api';

interface ParQFormProps {
  onSuccess: () => void;
}

const QUESTIONS = [
  { key: 'coeur', label: 'Un médecin vous a-t-il déjà dit que vous avez un problème cardiaque ?' },
  { key: 'douleur_effort', label: 'Ressentez-vous une douleur à la poitrine lorsque vous faites un effort ?' },
  { key: 'douleur_repos', label: 'Ressentez-vous une douleur à la poitrine lorsque vous ne faites pas d\'effort ?' },
  { key: 'os_articulations', label: 'Avez-vous des problèmes osseux ou articulaires ?' },
  { key: 'equilibre', label: 'Avez-vous déjà perdu l\'équilibre ou connaissance ?' },
  { key: 'medicaments', label: 'Prenez-vous des médicaments pour la tension ou le cœur ?' },
  { key: 'autre_medical', label: 'Y a-t-il une autre raison médicale qui pourrait vous limiter ?' },
];

export function ParQForm({ onSuccess }: ParQFormProps) {
  const [answers, setAnswers] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const hasWarning = Object.values(answers).some(Boolean);

  function toggleAnswer(key: string) {
    setAnswers((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    const parqAnswers = QUESTIONS.map((q) => ({
      question: q.label,
      answer: answers[q.key] || false,
    }));

    setLoading(true);
    try {
      await apiFetch('/api/onboarding/parq', {
        method: 'POST',
        body: JSON.stringify({ items: parqAnswers }),
      });
      setSubmitted(true);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-200">
          Questionnaire de préparation à l&apos;activité physique (PAR-Q)
        </h3>
        <p className="text-xs text-slate-400">
          Coche les cases qui s&apos;appliquent à toi
        </p>
      </div>

      <div className="space-y-3">
        {QUESTIONS.map((q) => (
          <label
            key={q.key}
            className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors cursor-pointer"
          >
            <input
              type="checkbox"
              checked={answers[q.key] || false}
              onChange={() => toggleAnswer(q.key)}
              className="mt-0.5 h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-slate-300">{q.label}</span>
          </label>
        ))}
      </div>

      {hasWarning && (
        <div className="p-3 rounded-lg bg-amber-950/50 border border-amber-800/50">
          <p className="text-sm text-amber-400">
            ⚠️ Consulte ton médecin avant de commencer un programme d&apos;entraînement.
          </p>
        </div>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Envoi...' : 'Terminer'}
      </Button>
    </form>
  );
}
