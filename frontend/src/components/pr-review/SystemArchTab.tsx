import { CheckCircle2, ShieldCheck, Zap } from "lucide-react";
import type { PullRequestReview } from "@/lib/api";

export function SystemArchTab({ pr }: { pr: PullRequestReview }) {
  const { systemArch } = pr;

  return (
    <div className="flex flex-col gap-5 select-none">
      {/* Topology Pipeline Diagram */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-5 shadow-sm">
        <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-sky-400" />
          Autonomous Pipeline Topology (Microservices Orchestration)
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
          {systemArch.nodes.map((node) => (
            <div
              key={node.id}
              className="bg-[#101520] border border-[#1e2738] rounded-xl p-3.5 flex flex-col justify-between relative group hover:border-sky-500/40 transition-all shadow-sm"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-[10px] font-mono text-sky-400 bg-sky-950/40 border border-sky-800/30 px-1.5 py-0.5 rounded">
                    :{node.port}
                  </span>
                </div>
                <div className="font-semibold text-xs text-slate-100 mb-1">
                  {node.name}
                </div>
                <div className="text-[11px] text-[#787777] line-clamp-2">
                  {node.role}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-[#182130] flex items-center justify-between text-[10px] font-mono text-[#787777]">
                <span>Latency</span>
                <span className="text-slate-300 font-semibold">{node.latencyMs}ms</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Consensus Engine Weight Breakdown */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-5 shadow-sm">
        <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Consensus Decision Formula &amp; Gate Rules
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono text-slate-300">
          <div className="bg-[#101520] border border-[#1a2333] rounded-lg p-4">
            <div className="text-slate-100 font-bold mb-2">Weighted Scoring Equation</div>
            <p className="text-[#8e9bb0] leading-relaxed mb-3">
              Score = 0.40 &times; (Security Status) + 0.20 &times; (Code Quality / 10) + 0.20 &times; (Architecture / 10) + 0.20 &times; (QA Coverage / 10)
            </p>
            <div className="text-emerald-400 font-semibold text-[11px]">
              Current Calculated Score: {pr.consensus.score} / 100 &rarr; Threshold (80) Met
            </div>
          </div>

          <div className="bg-[#101520] border border-[#1a2333] rounded-lg p-4">
            <div className="text-slate-100 font-bold mb-2">Non-Negotiable Blocking Gates</div>
            <ul className="space-y-1.5 text-[#8e9bb0]">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Zero CRITICAL severity vulnerabilities allowed.</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>QA test pass rate must be 100%.</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span>Minimum test coverage threshold: 80%.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
