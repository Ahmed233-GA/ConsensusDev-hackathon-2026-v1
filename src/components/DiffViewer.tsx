import { FileCode2 } from 'lucide-react';

interface DiffViewerProps {
  diffText: string;
  prNumber: number;
  branch: string;
  author: string;
  filesChanged: number;
  additions: number;
  deletions: number;
}

export function DiffViewer({
  diffText,
  prNumber,
  branch,
  author,
  filesChanged,
  additions,
  deletions,
}: DiffViewerProps) {
  const lines = diffText.split('\n');

  return (
    <div className="glass rounded-2xl border border-ink-700/70 overflow-hidden">
      <div className="px-5 py-3 border-b border-ink-700/60 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <FileCode2 className="w-4 h-4 text-brand-400" />
          <h3 className="text-[13px] font-semibold text-white">Code Diff</h3>
          <span className="text-[11px] text-ink-300 font-mono">#{prNumber}</span>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono">
          <span className="text-ink-300">{author}</span>
          <span className="text-ink-400">·</span>
          <span className="text-brand-400">{branch}</span>
          <span className="text-ink-400">·</span>
          <span className="text-teal-400">+{additions}</span>
          <span className="text-rose-400">-{deletions}</span>
          <span className="text-ink-400">·</span>
          <span className="text-ink-300">{filesChanged} file{filesChanged > 1 ? 's' : ''}</span>
        </div>
      </div>
      <div className="overflow-x-auto max-h-[340px] overflow-y-auto">
        <pre className="text-[11.5px] font-mono leading-relaxed">
          {lines.map((line, i) => {
            let cls = 'text-ink-200';
            if (line.startsWith('+++') || line.startsWith('---')) cls = 'text-brand-300 font-semibold';
            else if (line.startsWith('@@')) cls = 'text-teal-400/80 bg-teal-500/5';
            else if (line.startsWith('+')) cls = 'text-teal-300 bg-teal-500/8';
            else if (line.startsWith('-')) cls = 'text-rose-300 bg-rose-500/8';
            else if (line.startsWith('diff ')) cls = 'text-amber-400 font-semibold bg-ink-800/50';
            return (
              <div key={i} className={`px-5 py-[1px] ${cls}`}>
                <span className="select-none opacity-50 mr-3 inline-block w-7 text-right">
                  {i + 1}
                </span>
                {line || ' '}
              </div>
            );
          })}
        </pre>
      </div>
    </div>
  );
}
