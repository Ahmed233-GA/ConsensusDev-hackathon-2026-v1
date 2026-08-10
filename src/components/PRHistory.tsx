import { GitPullRequest, GitMerge, GitBranch, Clock, Check, X } from 'lucide-react';
import type { PRReview } from '@/lib/types';

interface PRHistoryProps {
  reviews: PRReview[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

const statusLabel: Record<string, string> = {
  queued: 'Queued',
  scanning: 'Scanning',
  reviewing: 'Agents debating',
  consensus: 'Consensus',
  completed: 'Completed',
};

export function PRHistory({ reviews, activeId, onSelect }: PRHistoryProps) {
  return (
    <div className="glass rounded-2xl border border-ink-700/70 overflow-hidden flex flex-col h-full">
      <div className="px-4 py-3.5 border-b border-ink-700/60 flex items-center justify-between">
        <h3 className="text-[13px] font-semibold text-white">PR Queue</h3>
        <span className="text-[10px] text-ink-300 font-mono">
          {reviews.length} processed
        </span>
      </div>
      <div className="divide-y divide-ink-800/80 overflow-y-auto flex-1 max-h-[460px]">
        {reviews.length === 0 && (
          <div className="px-4 py-8 text-center text-[12px] text-ink-300">
            No PRs yet. Run the demo to start a review.
          </div>
        )}
        {reviews.map((r) => {
          const isActive = r.id === activeId;
          const done = r.status === 'completed';
          const approved = r.consensus === 'approve';
          return (
            <button
              key={r.id}
              onClick={() => onSelect(r.id)}
              className={`w-full text-left px-4 py-3 transition-colors ${
                isActive ? 'bg-brand-500/8 border-l-2 border-l-brand-500' : 'hover:bg-ink-800/40 border-l-2 border-l-transparent'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                {done ? (
                  approved ? (
                    <GitMerge className="w-3.5 h-3.5 text-teal-400 flex-shrink-0" />
                  ) : (
                    <GitPullRequest className="w-3.5 h-3.5 text-rose-400 flex-shrink-0" />
                  )
                ) : (
                  <div className="w-3.5 h-3.5 rounded-full border-2 border-brand-400 border-t-transparent animate-spin-slow flex-shrink-0" />
                )}
                <span className="text-[12px] font-semibold text-white truncate">
                  #{r.prNumber} {r.title}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[10px] text-ink-300 font-mono ml-5.5">
                <GitBranch className="w-2.5 h-2.5" />
                <span className="truncate">{r.branch}</span>
              </div>
              <div className="flex items-center justify-between mt-1.5 ml-5.5">
                <span
                  className={`text-[10px] font-medium ${
                    done
                      ? approved
                        ? 'text-teal-400'
                        : 'text-rose-400'
                      : 'text-brand-400'
                  }`}
                >
                  {done ? (approved ? 'Approved' : 'Changes requested') : statusLabel[r.status] || r.status}
                </span>
                {done && (
                  <span className="flex items-center gap-1 text-[10px] text-ink-300">
                    <Clock className="w-2.5 h-2.5" />
                    {(r.reviewTimeMs / 1000).toFixed(1)}s
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
