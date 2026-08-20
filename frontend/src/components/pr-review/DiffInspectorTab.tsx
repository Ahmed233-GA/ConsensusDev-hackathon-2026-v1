import { FileCode, Plus, Minus } from "lucide-react";
import type { PullRequestReview } from "@/lib/api";

export function DiffInspectorTab({ pr }: { pr: PullRequestReview }) {
  const diffLines = pr.diffText.split("\n");

  return (
    <div className="flex flex-col gap-4 select-none">
      {/* Diff Meta Bar */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-2 text-slate-200">
          <FileCode className="w-4 h-4 text-sky-400" />
          <span className="font-semibold">services/auth/jwt_service.ts</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-800/30">
            <Plus className="w-3 h-3" /> 248 additions
          </span>
          <span className="inline-flex items-center gap-1 text-red-400 bg-red-950/30 px-2 py-0.5 rounded border border-red-800/30">
            <Minus className="w-3 h-3" /> 34 deletions
          </span>
        </div>
      </div>

      {/* Syntax Diff Viewer */}
      <div className="bg-[#0c1017] border border-[#1e2738] rounded-xl overflow-hidden font-mono text-xs shadow-inner">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <tbody>
              {diffLines.map((line, idx) => {
                let rowBg = "hover:bg-[#131924]";
                let textCol = "text-slate-300";
                let prefixSymbol = " ";

                if (line.startsWith("+") && !line.startsWith("+++")) {
                  rowBg = "bg-emerald-950/20 hover:bg-emerald-950/30";
                  textCol = "text-emerald-300 font-medium";
                  prefixSymbol = "+";
                } else if (line.startsWith("-") && !line.startsWith("---")) {
                  rowBg = "bg-red-950/20 hover:bg-red-950/30";
                  textCol = "text-red-300 font-medium";
                  prefixSymbol = "-";
                } else if (line.startsWith("@@")) {
                  rowBg = "bg-[#182233]/60";
                  textCol = "text-sky-400 font-semibold";
                  prefixSymbol = "@";
                } else if (line.startsWith("diff") || line.startsWith("index")) {
                  rowBg = "bg-[#101520]";
                  textCol = "text-[#787777]";
                }

                return (
                  <tr key={idx} className={`border-b border-[#141b26] ${rowBg} transition-colors`}>
                    <td className="w-12 px-3 py-1 text-right text-[11px] text-[#4a5568] select-none border-r border-[#192130]">
                      {idx + 1}
                    </td>
                    <td className="w-6 px-2 py-1 text-center select-none font-bold opacity-60">
                      {prefixSymbol !== " " ? prefixSymbol : ""}
                    </td>
                    <td className={`px-3 py-1 whitespace-pre ${textCol}`}>
                      {line}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
