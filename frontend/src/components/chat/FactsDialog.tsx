'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { apiFetch } from '@/lib/api';

interface Fact {
  id: string;
  fact: string;
  category: string;
  category_label: string;
  importance: number;
  created_at?: string;
}

interface FactsResponse {
  facts: Fact[];
  total: number;
}

interface FactsDialogProps {
  open: boolean;
  onClose: () => void;
}

/** Barre de progression colorée pour l'importance */
function ImportanceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    value >= 0.8 ? 'bg-emerald-500' :
    value >= 0.5 ? 'bg-amber-500' :
    'bg-slate-500';

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-slate-700 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] text-slate-500 w-6 text-right">{pct}%</span>
    </div>
  );
}

export function FactsDialog({ open, onClose }: FactsDialogProps) {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return;

    let cancelled = false;

    async function fetchFacts() {
      setLoading(true);
      setError('');
      try {
        const data = await apiFetch<FactsResponse>('/api/facts');
        if (!cancelled) setFacts(data.facts);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Erreur de chargement');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchFacts();
    return () => { cancelled = true; };
  }, [open]);

  // Grouper les faits par catégorie
  const grouped = facts.reduce((acc, fact) => {
    const cat = fact.category_label;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(fact);
    return acc;
  }, {} as Record<string, Fact[]>);

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>🧠 Faits enregistrés</DialogTitle>
          <DialogDescription>
            Ce que le coach a retenu de vos conversations. Extraits automatiquement tous les 5 messages.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="space-y-3 py-4">
            <Skeleton className="h-5 w-3/4 bg-slate-800" />
            <Skeleton className="h-5 w-full bg-slate-800" />
            <Skeleton className="h-5 w-2/3 bg-slate-800" />
            <Skeleton className="h-5 w-4/5 bg-slate-800" />
          </div>
        ) : error ? (
          <p className="text-red-400 text-sm py-4">{error}</p>
        ) : facts.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-4xl mb-3">🧠</p>
            <p className="text-slate-400 text-sm">
              Aucun fait enregistré pour l'instant.
            </p>
            <p className="text-slate-500 text-xs mt-2">
              Continuez à discuter avec le coach — les faits importants
              seront extraits automatiquement de vos conversations.
            </p>
          </div>
        ) : (
          <div className="space-y-5 py-2">
            {Object.entries(grouped).map(([category, items]) => (
              <div key={category}>
                <h3 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide">
                  {category}
                </h3>
                <div className="space-y-2">
                  {items.map((fact) => (
                    <div
                      key={fact.id}
                      className="rounded-lg bg-slate-800/70 px-3 py-2.5"
                    >
                      <p className="text-sm text-slate-200">{fact.fact}</p>
                      <div className="mt-1.5">
                        <ImportanceBar value={fact.importance} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
