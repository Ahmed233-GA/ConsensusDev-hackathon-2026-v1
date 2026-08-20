import { User, GitCommit, GitBranch, Copy, Check } from "lucide-react";
import * as React from "react";
import type { PRMeta } from "@/lib/api";

export interface PRHeaderBarProps {
  meta: PRMeta;
}

export function PRHeaderBar({ meta }: PRHeaderBarProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopyHash = () => {
    navigator.clipboard.writeText(meta.commitHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-wrap items-center gap-2 mb-5">
      {/* Author Pill */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs text-slate-200 font-medium select-none shadow-sm">
        <User className="w-3.5 h-3.5 text-[#787777]" />
        <span>{meta.author.username}</span>
      </div>

      {/* Commit Hash Pill */}
      <button
        type="button"
        onClick={handleCopyHash}
        title={`Commit: ${meta.commitHash} (Click to copy)`}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs font-mono text-slate-200 hover:border-slate-500/40 transition-colors select-none cursor-pointer group shadow-sm"
      >
        <GitCommit className="w-3.5 h-3.5 text-[#787777] group-hover:text-slate-300" />
        <span className="font-semibold">{meta.shortHash}</span>
        {copied ? (
          <Check className="w-3 h-3 text-emerald-400" />
        ) : (
          <Copy className="w-3 h-3 text-[#787777] opacity-0 group-hover:opacity-100 transition-opacity" />
        )}
      </button>

      {/* Source Branch Pill */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs font-mono text-slate-300 select-none shadow-sm">
        <GitBranch className="w-3.5 h-3.5 text-[#787777]" />
        <span className="text-[#787777]">source:</span>
        <span className="text-slate-100 font-semibold">{meta.sourceBranch}</span>
      </div>
    </div>
  );
}
