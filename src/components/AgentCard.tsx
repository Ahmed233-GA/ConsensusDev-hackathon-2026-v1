import {
  ShieldCheck,
  Wrench,
  BookOpen,
  Gauge,
  Check,
  X,
} from 'lucide-react';
import type { AgentVerdict } from '@/lib/types';

const agentIcon = (id: string) => {
  switch (id) {
    case 'security':
      return ShieldCheck;
    case 'tech_debt':
      return Wrench;
    case 'story':
      return BookOpen;
    case 'performance':
      return Gauge;
    default:
      return ShieldCheck;
  }
};

const agentColor = (id: string) => {
  switch (id) {
    case 'security':
      return { ring: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/25', label: 'SAST' };
    case 'tech_debt':
      return { ring: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/25', label: 'Quality' };
    case 'story':
      return { ring: 'text-brand-400', bg: 'bg-brand-500/10', border: 'border-brand-500/25', label: 'Spec' };
    case 'performance':
      return { ring: 'text-teal-400', bg: 'bg-teal-500/10', border: 'border-teal-500/25', label: 'Perf' };
    default:
      return { ring: 'text-ink-200', bg: 'bg-ink-800', border: 'border-ink-700', label: '' };
  }
};

interface AgentCardProps {
  agent: AgentVerdict;
  index: number;
  isThinking?: boolean;
}

export function AgentCard({ agent, index, isThinking }: AgentCardProps) {
  const Icon = agentIcon(agent.id);
  const c = agentColor(agent.id);
  const approved = agent.verdict === 'approve';

  return (
    <div
      className={`glass rounded-2xl border p-5 relative overflow-hidden transition-all animate-fade-up ${
        approved ? 'border-ink-700/70' : 'border-rose-500/30 glow-rose'
      }`}
      style={{ animationDelay: `${index * 120}ms` }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-lg ${c.bg} ${c.border} border flex items-center justify-center ${c.ring}`}
          >
            <Icon className="w-4.5 h-4.5" strokeWidth={2} />
          </div>
          <div>
            <div className="text-[13px] font-semibold text-white leading-tight">{agent.name}</div>
            <div className="text-[10px] uppercase tracking-wider text-ink-300 font-medium">
              {c.label}
            </div>
          </div>
        </div>
        {isThinking ? (
          <div className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-ink-300 animate-bounce-dot" />
            <span
              className="w-1.5 h-1.5 rounded-full bg-ink-300 animate-bounce-dot"
              style={{ animationDelay: '0.2s' }}
            />
            <span
              className="w-1.5 h-1.5 rounded-full bg-ink-300 animate-bounce-dot"
              style={{ animationDelay: '0.4s' }}
            />
          </div>
        ) : (
          <span
            className={`flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full ${
              approved
                ? 'bg-teal-500/15 text-teal-400 border border-teal-500/30'
                : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
            }`}
          >
            {approved ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            {approved ? 'APPROVE' : 'CHANGES'}
          </span>
        )}
      </div>

      <p className="text-[12.5px] leading-relaxed text-ink-100 min-h-[48px]">
        {isThinking ? <span className="text-ink-300 italic">Analyzing diff…</span> : agent.reason}
      </p>

      {!isThinking && (
        <div className="mt-3 pt-3 border-t border-ink-700/60 flex items-center justify-between">
          <span className="text-[10px] text-ink-300 uppercase tracking-wider font-medium">
            Confidence
          </span>
          <div className="flex items-center gap-2">
            <div className="w-20 h-1.5 rounded-full bg-ink-700 overflow-hidden">
              <div
                className={`h-full rounded-full ${approved ? 'bg-teal-400' : 'bg-rose-400'} transition-all duration-700`}
                style={{ width: isThinking ? '0%' : `${agent.confidence * 100}%` }}
              />
            </div>
            <span className="text-[11px] font-semibold text-ink-100 tabular-nums">
              {Math.round(agent.confidence * 100)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
