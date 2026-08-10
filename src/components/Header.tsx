import { GitMerge, Sparkles, Activity } from 'lucide-react';

interface HeaderProps {
  isLive: boolean;
  onReset: () => void;
}

export function Header({ isLive, onReset }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 glass border-b border-ink-700/60">
      <div className="max-w-[1400px] mx-auto px-5 md:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-teal-500 flex items-center justify-center glow-brand">
            <GitMerge className="w-5 h-5 text-white" strokeWidth={2.5} />
          </div>
          <div className="leading-tight">
            <div className="flex items-center gap-2">
              <h1 className="text-[17px] font-bold tracking-tight text-white">
                Consensus<span className="text-brand-400">Dev</span>
              </h1>
              <span className="hidden sm:inline text-[10px] font-semibold uppercase tracking-wider text-ink-300 bg-ink-800 px-2 py-0.5 rounded-full border border-ink-700">
                Multi-Agent
              </span>
            </div>
            <p className="text-[11px] text-ink-300 hidden sm:block">
              Autonomous PR Review &amp; Security Gate
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex items-center gap-2 text-xs text-ink-200">
            <Sparkles className="w-3.5 h-3.5 text-teal-400" />
            <span className="font-medium">claude-sonnet-4 · 4 agents</span>
          </div>
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
              isLive
                ? 'bg-teal-500/10 border-teal-500/40 text-teal-400'
                : 'bg-ink-800 border-ink-700 text-ink-300'
            }`}
          >
            <span className="relative flex w-2 h-2">
              {isLive && (
                <span className="absolute inline-flex h-full w-full rounded-full bg-teal-400 animate-pulse-ring" />
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  isLive ? 'bg-teal-400' : 'bg-ink-400'
                }`}
              />
            </span>
            {isLive ? 'Pipeline Live' : 'Idle'}
          </div>
          <button
            onClick={onReset}
            className="text-xs font-medium text-ink-200 hover:text-white border border-ink-700 hover:border-ink-500 px-3 py-1.5 rounded-lg transition-colors"
          >
            Reset
          </button>
        </div>
      </div>
    </header>
  );
}
