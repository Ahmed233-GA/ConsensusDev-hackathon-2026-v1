import { CheckCircle2, Activity, Clock, AlertTriangle } from "lucide-react";
import type { PullRequestReview } from "@/lib/api";
import { ProgressBar } from "@/components/ui/ProgressBar";

export function QATestTab({ pr }: { pr: PullRequestReview }) {
  const { qaStats } = pr;

  const isOnline = qaStats.status !== "UNKNOWN" && qaStats.status !== "OFFLINE";
  const passRate = qaStats.testsPassed + qaStats.testsFailed > 0
    ? Math.round((qaStats.testsPassed / (qaStats.testsPassed + qaStats.testsFailed)) * 100)
    : (isOnline ? 100 : 0);

  return (
    <div className="flex flex-col gap-5 select-none">
      {/* Top QA Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Tests Passed</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {isOnline ? qaStats.testsPassed : "N/A"}
            </span>
            <span className={`text-xs font-mono flex items-center gap-1 ${passRate === 100 && isOnline ? "text-emerald-400" : "text-amber-400"}`}>
              {isOnline ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" /> {passRate}% Pass Rate
                </>
              ) : (
                "Service Offline"
              )}
            </span>
          </div>
          <span className="text-[11px] text-[#787777]">
            {isOnline ? `${qaStats.testsFailed} failed, 0 skipped` : "QA evidence unavailable"}
          </span>
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Code Coverage</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {qaStats.coveragePercentage !== null && qaStats.coveragePercentage !== undefined ? `${qaStats.coveragePercentage.toFixed(1)}%` : "N/A"}
            </span>
            <span className="text-xs text-slate-300 font-mono">Target: &ge;80%</span>
          </div>
          <ProgressBar value={qaStats.coveragePercentage || 0} className="h-1 bg-[#101520] mt-1" />
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Mutation Score</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {qaStats.mutationScore !== null && qaStats.mutationScore !== undefined ? `${qaStats.mutationScore.toFixed(1)}%` : "N/A"}
            </span>
            <span className="text-xs text-sky-400 font-mono">Mutmut Analyzer</span>
          </div>
          <ProgressBar value={qaStats.mutationScore || 0} className="h-1 bg-[#101520] mt-1" />
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between">
          <span className="text-[11px] font-mono text-[#787777] uppercase">QA Runner</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-xl font-semibold text-slate-100">QA Service</span>
            <span className="text-xs text-[#787777] font-mono">:8003</span>
          </div>
          <span className={`text-[11px] flex items-center gap-1 ${isOnline ? "text-emerald-400" : "text-amber-400"}`}>
            {isOnline ? <Activity className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
            {isOnline ? "Service Online" : "Service Offline"}
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
            Execution Status: {qaStats.status}
          </span>
        </div>

        {qaStats.suites.length === 0 ? (
          <div className="p-8 text-center text-[#787777] font-mono text-xs">
            {isOnline ? "No individual test suites recorded in this diff." : "QA Runner service is offline. No suite results available."}
          </div>
        ) : (
          <div className="divide-y divide-[#182130]">
            {qaStats.suites.map((suite, idx) => (
              <div
                key={idx}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#18202d]/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <CheckCircle2 className={`w-4 h-4 shrink-0 ${suite.passed ? "text-emerald-400" : "text-red-400"}`} />
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
                  <span className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${suite.passed ? "text-emerald-400 bg-emerald-950/40 border border-emerald-800/40" : "text-red-400 bg-red-950/40 border border-red-800/40"}`}>
                    {suite.passed ? "PASS" : "FAIL"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
