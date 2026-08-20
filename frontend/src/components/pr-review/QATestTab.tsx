import { CheckCircle2, Activity, Clock } from "lucide-react";
import type { PullRequestReview } from "@/lib/api";
import { ProgressBar } from "@/components/ui/ProgressBar";

export function QATestTab({ pr }: { pr: PullRequestReview }) {
  const { qaStats } = pr;

  return (
    <div className="flex flex-col gap-5 select-none">
      {/* Top QA Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Tests Passed</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {qaStats.testsPassed}
            </span>
            <span className="text-xs text-emerald-400 font-mono flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> 100% Pass Rate
            </span>
          </div>
          <span className="text-[11px] text-[#787777]">0 failed, 0 skipped</span>
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Code Coverage</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {qaStats.coveragePercentage}%
            </span>
            <span className="text-xs text-slate-300 font-mono">Target: &gt;80%</span>
          </div>
          <ProgressBar value={qaStats.coveragePercentage} className="h-1 bg-[#101520] mt-1" />
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Mutation Score</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {qaStats.mutationScore}%
            </span>
            <span className="text-xs text-sky-400 font-mono">Mutmut v2.4</span>
          </div>
          <ProgressBar value={qaStats.mutationScore} className="h-1 bg-[#101520] mt-1" />
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">QA Runner</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-xl font-semibold text-slate-100">Shahd QA</span>
            <span className="text-xs text-[#787777] font-mono">:8003</span>
          </div>
          <span className="text-[11px] text-emerald-400 flex items-center gap-1">
            <Activity className="w-3 h-3" /> Service Online
          </span>
        </div>
      </div>

      {/* Test Suites Table */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-[#1e2738] flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Test Suite Breakdown
          </h4>
          <span className="text-xs text-[#787777] font-mono">
            Total Execution Time: 0.89s
          </span>
        </div>

        <div className="divide-y divide-[#182130]">
          {qaStats.suites.map((suite, idx) => (
            <div
              key={idx}
              className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#18202d]/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <div>
                  <div className="font-mono text-xs font-semibold text-slate-200">
                    {suite.name}
                  </div>
                  <div className="text-[11px] text-[#787777] flex items-center gap-2 mt-0.5">
                    <span>{suite.totalTests} tests</span>
                    <span>&bull;</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {suite.duration}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 w-full sm:w-48">
                <div className="flex-1">
                  <div className="flex justify-between text-[11px] font-mono mb-1">
                    <span className="text-[#787777]">Coverage</span>
                    <span className="text-slate-200">{suite.coverage}%</span>
                  </div>
                  <ProgressBar value={suite.coverage} className="h-1 bg-[#101520]" />
                </div>
                <span className="text-xs font-bold text-emerald-400 font-mono px-2 py-0.5 bg-emerald-950/40 border border-emerald-800/40 rounded">
                  PASS
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
