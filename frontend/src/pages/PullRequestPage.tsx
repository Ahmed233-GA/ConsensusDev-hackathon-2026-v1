import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { PRHeaderBar } from "@/components/pr-review/PRHeaderBar";
import { ConsensusScoreCard } from "@/components/pr-review/ConsensusScoreCard";
import { AgentScoreGrid } from "@/components/pr-review/AgentScoreCard";
import { FindingsTabs } from "@/components/pr-review/FindingsTabs";
import { getPullRequest, listPullRequests, triggerManualReview, type PullRequestReview } from "@/lib/api";
import { RefreshCw, ArrowLeft, Zap, AlertTriangle } from "lucide-react";

export function PullRequestPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [pr, setPr] = React.useState<PullRequestReview | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [triggering, setTriggering] = React.useState(false);

  const prId = id || "pr-142";

  const loadData = React.useCallback(async () => {
    try {
      let data = await getPullRequest(prId);
      if (!data) {
        // Fallback: check if any PR exists in list
        const allPrs = await listPullRequests();
        if (allPrs.length > 0) {
          data = allPrs[0];
        }
      }
      setPr(data);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [prId]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleTriggerDemo = async () => {
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
      setPr(result);
      navigate(`/pull-requests/${result.meta.id}`);
    } catch (err) {
      console.error("Failed to run review:", err);
      alert("Make sure Gateway (:8000) is running!");
    } finally {
      setTriggering(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <RefreshCw className="w-6 h-6 text-sky-400 animate-spin" />
        <span className="text-xs font-mono text-[#787777]">Loading Consensus PR Review...</span>
      </div>
    );
  }

  if (!pr) {
    return (
      <div className="p-12 text-center max-w-lg mx-auto">
        <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-3 opacity-80" />
        <h3 className="text-lg font-bold text-slate-100">Review Data Unavailable</h3>
        <p className="text-xs text-[#787777] mt-1 mb-5">
          No live review data was returned by the Gateway for <code>{prId}</code>.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => navigate("/pull-requests")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs text-slate-300 hover:text-white"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> All PRs
          </button>
          <button
            type="button"
            onClick={handleTriggerDemo}
            disabled={triggering}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition-colors"
          >
            <Zap className="w-3.5 h-3.5 fill-current" />
            <span>{triggering ? "Analyzing..." : "Trigger Live PR Review"}</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Top Header Row with Refresh */}
      <div className="flex items-center justify-between gap-4 mb-3">
        <PRHeaderBar meta={pr.meta} />
        <div className="flex items-center gap-2 mb-5">
          <button
            type="button"
            onClick={handleRefresh}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs font-medium text-slate-300 hover:text-white hover:border-[#2d3a52] transition-colors select-none cursor-pointer shadow-sm"
            title="Re-fetch PR Review & Live Findings"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Main Consensus Score Card */}
      <div id="section-security" className="scroll-mt-20">
        <ConsensusScoreCard consensus={pr.consensus} agents={pr.agents} />
      </div>

      {/* 4 Agent Score Cards Grid */}
      <div id="section-code_quality" className="scroll-mt-20">
        <AgentScoreGrid agents={pr.agents} />
      </div>

      {/* Findings Tabs (Security, QA, Diff, System Arch) */}
      <div id="section-architecture" className="scroll-mt-20">
        <div id="section-qa" className="scroll-mt-20">
          <div id="section-system_health" className="scroll-mt-20">
            <FindingsTabs pr={pr} />
          </div>
        </div>
      </div>
    </div>
  );
}
