import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, GitPullRequest } from "lucide-react";
import { listPullRequests, type PullRequestReview } from "@/lib/api";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Badge } from "@/components/ui/Badge";

export function DashboardPage() {
  const navigate = useNavigate();
  const [prs, setPrs] = React.useState<PullRequestReview[]>([]);

  React.useEffect(() => {
    listPullRequests().then(setPrs);
  }, []);

  const totalReviews = prs.length;
  const approvedCount = prs.filter((p) => p.consensus.decision === "approved").length;
  const approvalRate = totalReviews ? Math.round((approvedCount / totalReviews) * 100) : 0;
  const totalFindings = prs.reduce((acc, curr) => acc + curr.findings.length, 0);

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      {/* Title */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-100 font-headline">
          Consensus Analytics &amp; PR Gate Dashboard
        </h1>
        <p className="text-xs text-[#787777] mt-1">
          High-level operational overview of autonomous multi-agent review pipeline.
        </p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">PRs Reviewed</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {totalReviews}
            </span>
            <span className="text-xs text-sky-400 font-mono">Live Session</span>
          </div>
          <span className="text-[11px] text-[#787777]">Autonomous pipeline active</span>
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Approval Rate</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              {approvalRate}%
            </span>
            <span className="text-xs text-emerald-400 font-mono">Consensus threshold &ge; 80</span>
          </div>
          <ProgressBar value={approvalRate} className="h-1 bg-[#101520] mt-1" />
        </div>

        <div className="bg-[#151C28] border border-[#1e2738] rounded-xl p-4 flex flex-col justify-between shadow-sm">
          <span className="text-[11px] font-mono text-[#787777] uppercase">Avg Review Latency</span>
          <div className="flex items-baseline gap-2 my-1">
            <span className="text-3xl font-light text-white font-headline">
              3.4s
            </span>
            <span className="text-xs text-slate-300 font-mono">P95: 4.8s</span>
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
          <span className="text-[11px] text-[#787777]">Checkov, Trivy, SonarQube</span>
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
                    {p.meta.sourceBranch} &bull; {p.meta.author.username}
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
      </div>
    </div>
  );
}
