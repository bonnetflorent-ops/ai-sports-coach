'use client';

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  name: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  icon?: string;
}

export function MetricCard({ name, value, unit, trend, icon }: MetricCardProps) {
  const trendIcon =
    trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→';
  const trendColor =
    trend === 'up'
      ? 'text-emerald-400'
      : trend === 'down'
        ? 'text-red-400'
        : 'text-slate-400';

  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardContent className="flex flex-col gap-1 p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">{name}</span>
          {icon && <span className="text-lg">{icon}</span>}
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold text-slate-50">
            {typeof value === 'number' ? value.toLocaleString('fr-FR') : value}
          </span>
          <span className="text-sm text-slate-500">{unit}</span>
        </div>
        {trend && (
          <div className="flex items-center gap-1">
            <span className={cn('text-sm font-medium', trendColor)}>
              {trendIcon}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
