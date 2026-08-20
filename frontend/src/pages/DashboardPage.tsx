import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, GitPullRequest, RefreshCw, Zap, ShieldAlert } from "lucide-react";
import { listPullRequests, triggerManualReview, type PullRequestReview } from "@/lib/api";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Badge } from "@/components/ui/Badge";

export function DashboardPage() {
  const navigate = useNavigate();
  const [prs, setPrs] = React.useState<PullRequestReview[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [triggering, setTriggering] = React.useState(false);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await listPullRequests();
      setPrs(data);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunDemo = async () => {
    setTriggering(true);
    try {
      const sampleDiff = `diff --git a/services/auth.py b/services/auth.py
+++ b/services/auth.py
@@ -1,5 +1,8 @@
+def authenticate_user(username: str, token: str) -> bool:
+    if not username or not token:
+        return False
+    return len(token) >= 32
`;
      const result = await triggerManualReview(
        sampleDiff,
        142,
        "feat(auth): implement secure session token validation",
        "AhmedSoliman",
        "feature/secure-session"
      );
      await loadData();
      navigate(`/pull-requests/${result.meta.id}`);
    } catch (err) {
      console.error("Failed to run review:", err);
      alert("Make sure Gateway (:8000) is running!");
    } finally {
      setTriggering(false);
    }
  };

  const totalReviews = prs.length;
  const approvedCount = prs.filter((p) => p.consensus.decision === "approved").length;
  const approvalRate = totalReviews ? Math.round((approvedCount / totalReviews) * 100) : 0;
  const totalFindings = prs.reduce((acc, curr) => acc + (curr.findings?.length || 0), 0);

  // Real review latency calculation
  const latencies = prs.map((p) => p.reviewTimeSeconds || 0).filter((t) => t > 0);
  const avgLatencyStr = latencies.length
    ? `${(latencies.reduce((a, b) => a + b, 0) / latencies.length).toFixed(2)}s`
    : "N/A";
  const maxLatencyStr = latencies.length
    ? `${Math.max(...latencies).toFixed(2)}s`
    : "N/A";

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      {/* Title & Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-headline">
            Consensus Analytics &amp; PR Gate Dashboard
          </h1>
          <p className="text-xs text-[#787777] mt-1">
            High-level operational overview of autonomous multi-agent review pipeline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs text-slate-300 hover:text-white hover:border-[#2d3a52] transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
            <span>Sync</span>
          </button>
          <button
            type="button"
            onClick={handleRunDemo}
            disabled={triggering}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition-colors cursor-pointer shadow-md disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>{triggering ? "Analyzing..." : "Trigger Live Review"}</span>
          </button>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">PRs Reviewed</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {totalReviews}
            </span>
            <span className="text-xs text-sky-400 font-mono">Live Sessions</span>
          </div>
          <span className="text-[11px] text-[#787777]">Autonomous pipeline active</span>
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Approval Rate</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {totalReviews ? `${approvalRate}%` : "N/A"}
            </span>
            <span className="text-xs text-emerald-400 font-mono">Score &ge; 80</span>
          </div>
          <ProgressBar value={approvalRate} className="h-1 bg-[#101520] mt-1" />
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Avg Review Latency</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {avgLatencyStr}
            </span>
            <span className="text-xs text-slate-300 font-mono">Max: {maxLatencyStr}</span>
          </div>
          <span className="text-[11px] text-[#787777]">Parallel scanner execution</span>
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Vulnerabilities Caught</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {totalFindings}
            </span>
            <span className="text-xs text-[#fb923c] font-mono">SAST &amp; Secrets</span>
          </div>
          <span className="text-[11px] text-[#787777]">Checkov, Trivy, SAST</span>
        </div>
      </div>

      {/* Recent PR Activity */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-100 font-headline">
            Recent Review Stream
          </h3>
          <button
            type="button"
            onClick={() => navigate("/pull-requests")}
            className="text-xs text-sky-400 hover:underline flex items-center gap-1 cursor-pointer font-medium"
          >
            View all PRs <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {prs.length === 0 ? (
          <div className="p-8 text-center bg-[#101520] border border-[#182130] rounded-xl">
            <ShieldAlert className="w-8 h-8 text-[#787777] mx-auto mb-2 opacity-60" />
            <h4 className="text-sm font-semibold text-slate-200">No Pull Request Reviews Yet</h4>
            <p className="text-xs text-[#787777] mt-1 mb-4">
              Connect a GitHub Webhook to <code className="text-slate-300 bg-[#151c28] px-1 py-0.5 rounded">/webhook/github</code> or trigger a live demo review.
            </p>
            <button
              type="button"
              onClick={handleRunDemo}
              disabled={triggering}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-500 text-slate-950 font-semibold text-xs hover:bg-sky-400 transition-colors cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>Trigger Sample PR Review</span>
            </button>
          </div>
        ) : (
          <div className="divide-y divide-[#182130]">
            {prs.map((p) => (
              <div
                key={p.meta.id}
                onClick={() => navigate(`/pull-requests/${p.meta.id}`)}
                className="py-3.5 flex items-center justify-between gap-4 hover:bg-[#192232]/60 px-3 rounded-lg transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <GitPullRequest className="w-4 h-4 text-sky-400 shrink-0" />
                  <div>
                    <div className="text-xs font-semibold text-slate-200">
                      #{p.meta.prNumber} &bull; {p.meta.title}
                    </div>
                    <div className="text-[11px] font-mono text-[#787777] mt-0.5">
                      {p.meta.sourceBranch} &bull; @{p.meta.author.username}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-bold text-slate-200">
                    {p.consensus.score}/100
                  </span>
                  <Badge
                    variant={p.consensus.decision === "approved" ? "approved" : "rejected"}
                    className="text-[10px] px-2 py-0.5"
                  >
                    {p.consensus.decision.toUpperCase()}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
