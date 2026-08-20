import * as React from "react";
import { Play, CheckCircle2, RefreshCw } from "lucide-react";

export function PipelinesPage() {
  const [running, setRunning] = React.useState(false);
  const [step, setStep] = React.useState(5);

  const pipelineSteps = [
    { title: "GitHub Webhook Ingestion", service: "Gateway (:8000)", latency: "14ms", status: "completed" },
    { title: "Parallel Soliman SAST/Checkov Scans", service: "Security Scanner (:8002)", latency: "82ms", status: "completed" },
    { title: "Shahd QA Test Runner & Mutation Test", service: "QA Runner (:8003)", latency: "120ms", status: "completed" },
    { title: "Medhat AI Multi-Agent LLM Evaluation", service: "AI Engine (:8001)", latency: "340ms", status: "completed" },
    { title: "Consensus Aggregation & PR Status Published", service: "Consensus Engine", latency: "12ms", status: "completed" },
  ];

  const handleSimulate = () => {
    setRunning(true);
    setStep(1);
    const interval = setInterval(() => {
      setStep((prev) => {
        if (prev >= 5) {
          clearInterval(interval);
          setRunning(false);
          return 5;
        }
        return prev + 1;
      });
    }, 600);
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-headline">
            Autonomous Pipeline Execution
          </h1>
          <p className="text-xs text-[#787777] mt-1">
            End-to-end webhook orchestration pipeline and microservice latency breakdown.
          </p>
        </div>

        <button
          type="button"
          onClick={handleSimulate}
          disabled={running}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 text-slate-900 font-semibold text-xs hover:bg-white active:bg-slate-200 transition-all cursor-pointer shadow-md disabled:opacity-50"
        >
          {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          <span>{running ? "Executing Review Pipeline..." : "Trigger Pipeline Simulation"}</span>
        </button>
      </div>

      {/* Pipeline Steps List */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-2xl p-6 mb-6 shadow-sm">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono mb-6">
          Pipeline Execution Stages
        </h3>

        <div className="space-y-4">
          {pipelineSteps.map((s, idx) => {
            const isDone = step > idx;
            const isCurrent = step === idx + 1 && running;

            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  isCurrent
                    ? "bg-[#182335] border-sky-500/50 shadow-md shadow-sky-950/40"
                    : isDone
                    ? "bg-[#101520] border-[#1d273a]"
                    : "bg-[#0d1118] border-[#151c27] opacity-40"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs font-bold ${
                      isDone
                        ? "bg-emerald-950/60 text-emerald-400 border border-emerald-700/50"
                        : isCurrent
                        ? "bg-sky-950/60 text-sky-400 border border-sky-500 animate-pulse"
                        : "bg-[#141b26] text-[#787777] border border-[#1e2738]"
                    }`}
                  >
                    {isDone ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                  </div>
                  <div>
                    <div className="font-semibold text-xs text-slate-100">
                      {s.title}
                    </div>
                    <div className="text-[11px] font-mono text-[#787777]">
                      {s.service}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 self-end sm:self-auto font-mono text-xs">
                  <span className="text-[#787777]">Latency: {s.latency}</span>
                  <span
                    className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      isDone
                        ? "text-emerald-400 bg-emerald-950/40 border border-emerald-800/40"
                        : isCurrent
                        ? "text-sky-400 bg-sky-950/40 border border-sky-800/40"
                        : "text-[#787777] bg-[#121822]"
                    }`}
                  >
                    {isDone ? "PASSED" : isCurrent ? "RUNNING" : "QUEUED"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
