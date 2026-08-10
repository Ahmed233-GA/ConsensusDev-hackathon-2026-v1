import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  icon: ReactNode;
  accent: 'brand' | 'teal' | 'amber' | 'rose';
  trend?: 'up' | 'down' | 'flat';
  trendLabel?: string;
  index?: number;
}

const accentMap = {
  brand: { ring: 'text-brand-400', bg: 'bg-brand-500/10', border: 'border-brand-500/20' },
  teal: { ring: 'text-teal-400', bg: 'bg-teal-500/10', border: 'border-teal-500/20' },
  amber: { ring: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  rose: { ring: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20' },
};

export function MetricCard({
  label,
  value,
  sub,
  icon,
  accent,
  trend,
  trendLabel,
  index = 0,
}: MetricCardProps) {
  const a = accentMap[accent];
  return (
    <div
      className="glass rounded-2xl border border-ink-700/70 p-5 relative overflow-hidden animate-fade-up hover:border-ink-600 transition-colors"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-start justify-between">
        <div
          className={`w-10 h-10 rounded-xl ${a.bg} ${a.border} border flex items-center justify-center ${a.ring}`}
        >
          {icon}
        </div>
        {trend && trendLabel && (
          <div
            className={`flex items-center gap-1 text-[11px] font-semibold ${
              trend === 'up'
                ? 'text-teal-400'
                : trend === 'down'
                  ? 'text-rose-400'
                  : 'text-ink-300'
            }`}
          >
            {trend === 'up' ? '▲' : trend === 'down' ? '▼' : '■'} {trendLabel}
          </div>
        )}
      </div>
      <div className="mt-4">
        <div className="text-3xl font-bold text-white tracking-tight tabular-nums">{value}</div>
        <div className="text-[12px] text-ink-200 mt-1 font-medium">{label}</div>
        {sub && <div className="text-[11px] text-ink-300 mt-0.5">{sub}</div>}
      </div>
    </div>
  );
}
