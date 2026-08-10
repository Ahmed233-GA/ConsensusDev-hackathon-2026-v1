import { GitPullRequest, ScanLine, Bot, GitMerge } from 'lucide-react';
import type { PRStatus } from '@/lib/types';

interface PipelineProps {
  status: PRStatus;
}

const steps: { key: PRStatus; label: string; icon: typeof GitPullRequest }[] = [
  { key: 'queued', label: 'Webhook', icon: GitPullRequest },
  { key: 'scanning', label: 'Static Scan', icon: ScanLine },
  { key: 'reviewing', label: 'AI Agents', icon: Bot },
  { key: 'consensus', label: 'Consensus', icon: GitMerge },
];

export function Pipeline({ status }: PipelineProps) {
  const order: PRStatus[] = ['queued', 'scanning', 'reviewing', 'consensus', 'completed'];
  const currentIdx = order.indexOf(status);

  return (
    <div className="glass rounded-2xl border border-ink-700/70 p-5">
      <div className="flex items-center justify-between">
        {steps.map((step, i) => {
          const stepIdx = order.indexOf(step.key);
          const isDone = currentIdx > stepIdx;
          const isActive = status === step.key || (status === 'completed' && i === steps.length - 1);
          const Icon = step.icon;
          return (
            <div key={step.key} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`relative w-11 h-11 rounded-xl flex items-center justify-center border transition-all duration-500 ${
                    isDone || isActive
                      ? 'bg-teal-500/15 border-teal-500/40 text-teal-400'
                      : 'bg-ink-800 border-ink-700 text-ink-400'
                  }`}
                >
                  {isActive && (
                    <span className="absolute inset-0 rounded-xl border-2 border-teal-400/40 animate-pulse-ring" />
                  )}
                  <Icon className={`w-5 h-5 ${isActive ? 'animate-pulse' : ''}`} />
                </div>
                <span
                  className={`text-[10px] font-semibold uppercase tracking-wider ${
                    isDone || isActive ? 'text-teal-400' : 'text-ink-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div className="flex-1 h-[2px] mx-2 rounded-full bg-ink-800 relative overflow-hidden">
                  <div
                    className={`absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-teal-500 to-brand-500 transition-all duration-700 ${
                      currentIdx > stepIdx ? 'w-full' : isActive ? 'w-1/2' : 'w-0'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
