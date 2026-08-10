import { GitMerge, GitPullRequest, Check, X } from 'lucide-react';
import type { PRReview } from '@/lib/types';

interface ConsensusBannerProps {
  review: PRReview;
}

export function ConsensusBanner({ review }: ConsensusBannerProps) {
  const approved = review.consensus === 'approve';

  return (
    <div
      className={`rounded-2xl border p-5 flex items-center gap-4 animate-fade-up relative overflow-hidden ${
        approved
          ? 'bg-gradient-to-r from-teal-500/10 to-transparent border-teal-500/30 glow-teal'
          : 'bg-gradient-to-r from-rose-500/10 to-transparent border-rose-500/30 glow-rose'
      }`}
    >
      <div
        className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${
          approved ? 'bg-teal-500/15 text-teal-400' : 'bg-rose-500/15 text-rose-400'
        }`}
      >
        {approved ? <GitMerge className="w-7 h-7" /> : <GitPullRequest className="w-7 h-7" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
              approved ? 'bg-teal-500/15 text-teal-400' : 'bg-rose-500/15 text-rose-400'
            }`}
          >
            {approved ? 'CONSENSUS: APPROVE' : 'CONSENSUS: REQUEST CHANGES'}
          </span>
          <span className="text-[11px] text-ink-300 font-mono">
            #{review.prNumber} · {review.branch}
          </span>
        </div>
        <p className="text-sm text-white font-semibold mt-1.5 truncate">
          {review.title}
        </p>
        <p className="text-[12px] text-ink-200 mt-0.5">{review.consensusReason}</p>
      </div>
      <div className={`flex items-center gap-1.5 ${approved ? 'text-teal-400' : 'text-rose-400'}`}>
        {approved ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
      </div>
    </div>
  );
}
