'use client';

import { useState, useEffect, useCallback } from 'react';
import { AthleteModel } from '@/types';
import { apiFetch } from '@/lib/api';

export function useAthleteModel() {
  const [model, setModel] = useState<AthleteModel | null>(null);
  const [version, setVersion] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function fetchModel() {
      try {
        setLoading(true);
        const data = await apiFetch<{ model: AthleteModel; version: string }>(
          '/api/athlete/model',
        );
        if (!cancelled) {
          setModel(data.model);
          setVersion(data.version);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Erreur de chargement');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchModel();
    return () => { cancelled = true; };
  }, []);

  const patchField = useCallback(async (path: string, value: unknown) => {
    try {
      const data = await apiFetch<{ model: AthleteModel; version: string }>(
        '/api/athlete/model',
        {
          method: 'PATCH',
          body: JSON.stringify({ path, value }),
        },
      );
      setModel(data.model);
      setVersion(data.version);
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Erreur de mise à jour');
    }
  }, []);

  return { model, version, loading, error, patchField };
}
