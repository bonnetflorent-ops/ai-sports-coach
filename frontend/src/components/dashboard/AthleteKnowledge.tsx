'use client';

import { useState } from 'react';
import { useAthleteModel } from '@/hooks/useAthleteModel';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface AthleteKnowledgeProps {
  open: boolean;
  onClose: () => void;
}

const SECTION_LABELS: Record<string, string> = {
  physique: 'Physique',
  etat_actuel: 'État actuel',
  blessures: 'Blessures',
  preferences: 'Préférences',
  patterns: 'Patterns',
  objectifs: 'Objectifs',
};

const SECTION_ICONS: Record<string, string> = {
  physique: '💪',
  etat_actuel: '❤️',
  blessures: '🩹',
  preferences: '⚙️',
  patterns: '📈',
  objectifs: '🎯',
};

function getSourceIcon(field: unknown): string {
  if (typeof field !== 'object' || field === null) return '🧠';
  const f = field as Record<string, unknown>;
  const source = f.source as string | undefined;
  if (!source) return '🧠';
  switch (source) {
    case 'measured': return '📟';
    case 'reported': return '💬';
    case 'estimated': return '🧠';
    case 'corrected': return '✏️';
    default: return '🧠';
  }
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return '—';
    }
  }
  return String(value);
}

function isFieldEntry(value: unknown): boolean {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return 'value' in v || 'source' in v || 'date' in v;
}

function renderFieldValue(key: string, value: unknown) {
  const record = typeof value === 'object' && value !== null
    ? (value as Record<string, unknown>)
    : null;
  const val = record?.value ?? value;
  const date = typeof record?.date === 'string' ? record.date : null;

  return (
    <div key={key} className="flex items-start justify-between py-1.5">
      <div className="flex-1">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-slate-400 capitalize">
            {key.replace(/_/g, ' ')}
          </span>
          <span title="Source">
            {getSourceIcon(value)}
          </span>
        </div>
        <p className="text-sm text-slate-50 mt-0.5">
          {formatValue(val)}
        </p>
      </div>
      {date && (
        <span className="text-xs text-slate-500 shrink-0 ml-2">
          {date}
        </span>
      )}
    </div>
  );
}

function renderArrayField(items: Record<string, unknown>[], label: string) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-slate-500 py-2">Aucune information</p>;
  }
  return (
    <div className="space-y-2 py-1">
      {items.map((item, idx) => (
        <div key={idx} className="text-sm text-slate-300 bg-slate-800/50 rounded-lg p-2">
          {Object.entries(item).map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-slate-500 capitalize text-xs">{k}:</span>
              <span>{formatValue(v)}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export function AthleteKnowledge({ open, onClose }: AthleteKnowledgeProps) {
  const { model, loading, error } = useAthleteModel();
  const [expanded, setExpanded] = useState(false);

  const sections = model
    ? [
        { key: 'physique', data: model.physique },
        { key: 'etat_actuel', data: model.etat_actuel },
        { key: 'blessures', data: model.blessures as unknown as Record<string, unknown>[] },
        { key: 'preferences', data: model.preferences },
        { key: 'patterns', data: model.patterns as unknown as Record<string, unknown>[] },
        { key: 'objectifs', data: model.objectifs },
      ]
    : [];

  const visibleSections = expanded ? sections : sections.slice(0, 3);

  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent side="right" className="w-full max-w-sm sm:max-w-md">
        <SheetHeader className="mb-4">
          <div className="flex items-center gap-2">
            <SheetTitle className="text-slate-50">Modèle Athlète</SheetTitle>
            {model && (
              <Badge variant="outline" className="text-xs">
                v{model.meta?.version as string || '1'}
              </Badge>
            )}
          </div>
          <SheetDescription>
            Connaissances que le coach a sur toi
          </SheetDescription>
        </SheetHeader>

        {loading && (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="animate-pulse space-y-2">
                <div className="h-4 w-24 bg-slate-800 rounded" />
                <div className="h-3 w-full bg-slate-800/50 rounded" />
                <div className="h-3 w-3/4 bg-slate-800/50 rounded" />
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <p className="text-sm text-red-400 mb-2">Erreur de chargement</p>
            <Button variant="outline" size="sm" onClick={onClose}>
              Fermer
            </Button>
          </div>
        )}

        {!loading && !error && model && (
          <>
            <ScrollArea className="flex-1 -mx-6 px-6">
              <div className="space-y-6">
                {visibleSections.map(({ key, data }) => (
                  <div key={key}>
                    <div className="flex items-center gap-2 mb-2">
                      <span>{SECTION_ICONS[key] || '📋'}</span>
                      <h3 className="text-sm font-semibold text-slate-200">
                        {SECTION_LABELS[key] || key}
                      </h3>
                    </div>
                    {key === 'blessures' || key === 'patterns' ? (
                      renderArrayField(data as unknown as Record<string, unknown>[], SECTION_LABELS[key])
                    ) : (
                      <div className={cn(
                        'space-y-0 divide-y divide-slate-800/50',
                        Object.keys(data || {}).length === 0 && 'space-y-0'
                      )}>
                        {data && typeof data === 'object' && Object.keys(data).length > 0
                          ? Object.entries(data).map(([k, v]) =>
                              isFieldEntry(v)
                                ? renderFieldValue(k, v)
                                : (
                                    <div key={k} className="py-1.5">
                                      <span className="text-xs text-slate-400 capitalize block">
                                        {k.replace(/_/g, ' ')}
                                      </span>
                                      <p className="text-sm text-slate-50 mt-0.5">
                                        {formatValue(v)}
                                      </p>
                                    </div>
                                  )
                          )
                          : <p className="text-sm text-slate-500 py-2">Aucune information</p>
                        }
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>

            {sections.length > 3 && (
              <div className="mt-4 pt-4 border-t border-slate-800">
                <Button
                  variant="ghost"
                  className="w-full text-sm text-blue-400"
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? 'Voir moins' : 'Voir tout'}
                </Button>
              </div>
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
