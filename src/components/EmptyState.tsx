import { GitMerge, Play, Sparkles } from 'lucide-react';

interface EmptyStateProps {
  onRunDemo: () => void;
  isRunning: boolean;
}

export function EmptyState({ onRunDemo, isRunning }: EmptyStateProps) {
  return (
    <div className="glass rounded-2xl border border-ink-700/70 p-12 flex flex-col items-center text-center relative overflow-hidden">
      <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />
      <div className="relative">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-brand-500 to-teal-500 flex items-center justify-center glow-brand mx-auto mb-5">
          <GitMerge className="w-10 h-10 text-white" strokeWidth={2} />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Multi-Agent PR Review</h2>
        <p className="text-[13px] text-ink-200 max-w-md mx-auto leading-relaxed mb-6">
          Four specialized AI agents — Security, Technical Debt, Story Matching, and Performance —
          debate every pull request and reach a consensus decision in seconds.
        </p>
        <button
          onClick={onRunDemo}
          disabled={isRunning}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-teal-500 text-white font-semibold text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          <Play className="w-4 h-4" fill="currentColor" />
          {isRunning ? 'Running demo…' : 'Run Live Demo'}
        </button>
        <div className="flex items-center gap-2 mt-5 text-[11px] text-ink-300">
          <Sparkles className="w-3.5 h-3.5 text-teal-400" />
          <span>3 sample PRs · clean, risky, and performance-optimized</span>
        </div>
      </div>
    </div>
  );
}
