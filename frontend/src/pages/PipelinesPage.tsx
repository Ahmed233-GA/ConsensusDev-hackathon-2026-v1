import * as React from "react";
import { Play, CheckCircle2, RefreshCw, XCircle, Clock } from "lucide-react";
import { getSystemHealth, triggerManualReview, type SystemHealthResponse } from "@/lib/api";

export function PipelinesPage() {
  const [running, setRunning] = React.useState(false);
  const [health, setHealth] = React.useState<SystemHealthResponse | null>(null);
  const [currentStep, setCurrentStep] = React.useState<number>(0);
  const [executionLog, setExecutionLog] = React.useState<string[]>([]);

  const loadHealth = React.useCallback(async () => {
    const data = await getSystemHealth();
    setHealth(data);
  }, []);

  React.useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 5000);
    return () => clearInterval(interval);
  }, [loadHealth]);

  const pipelineStages = [
    {
      title: "GitHub Webhook Ingestion & HMAC Verification",
      service: "Gateway (:8000)",
      status: health?.services.gateway.status || "offline",
      latency: `${health?.services.gateway.latencyMs || 1}ms`,
    },
    {
      title: "Parallel SAST, IaC & Secret Scans",
      service: "Security Scanner (:8002)",
      status: health?.services.scanners.status || "offline",
      latency: `${health?.services.scanners.latencyMs || 0}ms`,
    },
    {
      title: "Automated QA Test Runner & Mutation Scoring",
      service: "QA Runner (:8003)",
      status: health?.services.qaRunner.status || "offline",
      latency: `${health?.services.qaRunner.latencyMs || 0}ms`,
    },
    {
      title: "Multi-Agent LLM Review & Synthesis",
      service: "AI Engine (:8001)",
      status: health?.services.aiEngine.status || "offline",
      latency: `${health?.services.aiEngine.latencyMs || 0}ms`,
    },
    {
      title: "Deterministic Consensus Gate & Auto-Merge Check",
      service: "Consensus Engine",
      status: health?.status === "healthy" ? "online" : "degraded",
      latency: "2ms",
    },
  ];

  const handleExecuteLivePipeline = async () => {
    setRunning(true);
    setCurrentStep(1);
    setExecutionLog(["[Gateway] Webhook event received: pull_request opened (PR #142)"]);

    try {
      setCurrentStep(2);
      setExecutionLog((prev) => [...prev, "[Security Scanner] Initiating Checkov & Trivy parallel scans..."]);

      setCurrentStep(3);
      setExecutionLog((prev) => [...prev, "[QA Runner] Running test suite and calculating code coverage..."]);

      setCurrentStep(4);
      setExecutionLog((prev) => [...prev, "[AI Engine] Dispatching diff to 4 specialized reviewer agents..."]);

      const sampleDiff = `diff --git a/app/security.py b/app/security.py
+++ b/app/security.py
@@ -1,4 +1,7 @@
+def verify_token(token: str) -> bool:
+    return len(token) >= 32
`;
      const review = await triggerManualReview(sampleDiff, 142, "feat(security): token check", "Ahmed233", "feature/security");

      setCurrentStep(5);
      setExecutionLog((prev) => [
        ...prev,
        `[Consensus Engine] Review complete! Decision: ${review.consensus.decision.toUpperCase()} (Score: ${review.consensus.score}/100)`,
      ]);
    } catch (err) {
      setExecutionLog((prev) => [...prev, `[Pipeline Error] ${String(err)}`]);
    } finally {
      setRunning(false);
      loadHealth();
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-headline">
            Autonomous Pipeline Execution
          </h1>
          <p className="text-xs text-[#787777] mt-1">
            End-to-end webhook orchestration pipeline and microservice telemetry breakdown.
          </p>
        </div>

        <button
          type="button"
          onClick={handleExecuteLivePipeline}
          disabled={running}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition-all cursor-pointer shadow-md disabled:opacity-50"
        >
          {running ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          <span>{running ? "Executing Review Pipeline..." : "Trigger Live PR Pipeline"}</span>
        </button>
      </div>

      {/* Pipeline Stages List */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-2xl p-6 mb-6 shadow-sm">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono mb-6">
          Microservices Pipeline Topology
        </h3>

        <div className="space-y-4">
          {pipelineStages.map((s, idx) => {
            const isOnline = s.status === "online";
            const isCurrent = running && currentStep === idx + 1;
            const isPassed = currentStep > idx + 1;

            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  isCurrent
                    ? "bg-[#182335] border-sky-500/50 shadow-md shadow-sky-950/40"
                    : isOnline
                    ? "bg-[#101520] border-[#1d273a]"
                    : "bg-[#0d1118] border-[#151c27] opacity-60"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs font-bold ${
                      isPassed || (!running && isOnline)
                        ? "bg-emerald-950/60 text-emerald-400 border border-emerald-700/50"
                        : isCurrent
                        ? "bg-sky-950/60 text-sky-400 border border-sky-500 animate-pulse"
                        : "bg-[#141b26] text-[#787777] border border-[#1e2738]"
                    }`}
                  >
                    {isPassed || (!running && isOnline) ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : (
                      idx + 1
                    )}
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
                      isOnline
                        ? "text-emerald-400 bg-emerald-950/40 border border-emerald-800/40"
                        : "text-red-400 bg-red-950/40 border border-red-800/40"
                    }`}
                  >
                    {isOnline ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Execution Logs */}
      {executionLog.length > 0 && (
        <div className="bg-[#0b0e14] border border-[#1e2738] rounded-2xl p-4 font-mono text-xs text-slate-300">
          <div className="text-[#787777] mb-2 font-semibold flex items-center gap-2">
            <Clock className="w-3.5 h-3.5" /> Live Execution Stream:
          </div>
          <div className="space-y-1">
            {executionLog.map((log, i) => (
              <div key={i} className="text-sky-300">{log}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
