import { Sparkles, Shapes, Tag, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface IconActionsProps {
  className?: string;
  onAiAction?: () => void;
  onShapeAction?: () => void;
  onTagAction?: () => void;
  onDeleteAction?: () => void;
}

export function IconActions({
  className,
  onAiAction,
  onShapeAction,
  onTagAction,
  onDeleteAction,
}: IconActionsProps) {
  return (
    <div className={cn("inline-flex items-center gap-1.5", className)}>
      <button
        type="button"
        onClick={onAiAction}
        className="w-7 h-7 rounded bg-[#131b2a] border border-[#1e293f] hover:bg-[#1a253a] hover:border-sky-500/40 text-sky-400 flex items-center justify-center transition-all cursor-pointer"
        title="AI Auto-fix Suggestion"
      >
        <Sparkles className="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        onClick={onShapeAction}
        className="w-7 h-7 rounded bg-[#161a24] border border-[#232a3b] hover:bg-[#1f2535] hover:border-purple-500/40 text-purple-400 flex items-center justify-center transition-all cursor-pointer"
        title="View Dependency Trace"
      >
        <Shapes className="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        onClick={onTagAction}
        className="w-7 h-7 rounded bg-[#171b22] border border-[#252c38] hover:bg-[#202732] hover:border-emerald-500/40 text-emerald-400 flex items-center justify-center transition-all cursor-pointer"
        title="Label / Classify Rule"
      >
        <Tag className="w-3.5 h-3.5" />
      </button>
      <button
        type="button"
        onClick={onDeleteAction}
        className="w-7 h-7 rounded bg-[#221014] border border-[#4a161e] hover:bg-[#30141b] hover:border-red-500/50 text-red-400 flex items-center justify-center transition-all cursor-pointer"
        title="Dismiss / Ignore Finding"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
