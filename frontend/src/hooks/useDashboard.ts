'use client';

import { useState, useEffect } from 'react';
import { MetricValue, ChartPoint } from '@/types';
import { apiFetch } from '@/lib/api';

interface DashboardMetrics {
  metrics: MetricValue[];
  chart: ChartPoint[];
  recap: string;
}

export function useDashboard() {
  const [metrics, setMetrics] = useState<MetricValue[]>([]);
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [recap, setRecap] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setLoading(true);
        const [metricsData, chartData, recapData] = await Promise.all([
          apiFetch<{ metrics: MetricValue[] }>('/api/dashboard/metrics'),
          apiFetch<{ chart: ChartPoint[] }>('/api/dashboard/chart?period=30d'),
          apiFetch<{ recap: string }>('/api/dashboard/recap'),
        ]);

        if (!cancelled) {
          setMetrics(metricsData.metrics);
          setChartData(chartData.chart);
          setRecap(recapData.recap);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Erreur de chargement');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchData();
    return () => { cancelled = true; };
  }, []);

  return { metrics, chartData, recap, loading, error };
}
