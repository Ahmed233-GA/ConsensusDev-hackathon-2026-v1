import * as React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { PRHeaderBar } from "@/components/pr-review/PRHeaderBar";
import { ConsensusScoreCard } from "@/components/pr-review/ConsensusScoreCard";
import { AgentScoreGrid } from "@/components/pr-review/AgentScoreCard";
import { FindingsTabs } from "@/components/pr-review/FindingsTabs";
import { getPullRequest, type PullRequestReview } from "@/lib/api";
import { RefreshCw, ArrowLeft } from "lucide-react";

export function PullRequestPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [pr, setPr] = React.useState<PullRequestReview | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);

  const prId = id || "pr-1248";

  const loadData = React.useCallback(async () => {
    try {
      const data = await getPullRequest(prId);
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
      <div className="p-8 text-center">
        <h3 className="text-lg font-bold text-slate-100">Pull Request Not Found</h3>
        <p className="text-xs text-[#787777] mt-1 mb-4">The requested review ID does not exist.</p>
        <button
          type="button"
          onClick={() => navigate("/pull-requests")}
          className="inline-flex items-center gap-2 text-xs text-sky-400 hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Pull Requests
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Top Header Row with Refresh */}
      <div className="flex items-center justify-between gap-4 mb-3">
        <PRHeaderBar meta={pr.meta} />
        <button
          type="button"
          onClick={handleRefresh}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs font-medium text-slate-300 hover:text-white hover:border-[#2d3a52] transition-colors select-none cursor-pointer mb-5 shadow-sm"
          title="Re-fetch PR Review & Live Findings"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
          <span>Sync Review</span>
        </button>
      </div>

      {/* Main Consensus Score Card */}
      <div id="section-security" className="scroll-mt-20">
        <ConsensusScoreCard consensus={pr.consensus} />
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
