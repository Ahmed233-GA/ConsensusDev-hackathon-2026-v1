import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, GitPullRequest, RefreshCw, Zap } from "lucide-react";
import { listPullRequests, triggerManualReview, type PullRequestReview } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { SearchInput } from "@/components/ui/SearchInput";

export function PullRequestsListPage() {
  const navigate = useNavigate();
  const [prs, setPrs] = React.useState<PullRequestReview[]>([]);
  const [query, setQuery] = React.useState("");
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

  const filteredPrs = prs.filter(
    (p) =>
      p.meta.title.toLowerCase().includes(query.toLowerCase()) ||
      p.meta.sourceBranch.toLowerCase().includes(query.toLowerCase()) ||
      p.meta.author.username.toLowerCase().includes(query.toLowerCase()) ||
      String(p.meta.prNumber).includes(query)
  );

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-headline">
            Pull Request Reviews
          </h1>
          <p className="text-xs text-[#787777] mt-1">
            Autonomous multi-agent evaluations and consensus verdicts across active repositories.
          </p>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="w-full sm:w-64">
            <SearchInput
              placeholder="Search PR by title, branch, or author..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-lg bg-[#151C28] border border-[#1e2738] text-slate-300 hover:text-white hover:border-[#2d3a52] transition-colors cursor-pointer"
            title="Refresh PR List"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
          </button>
        </div>
      </div>

      {/* PR Table List */}
      <div className="bg-[#151C28] border border-[#1e2738] rounded-2xl overflow-hidden shadow-sm">
        {prs.length === 0 ? (
          <div className="p-12 text-center">
            <GitPullRequest className="w-10 h-10 text-[#787777] mx-auto mb-3 opacity-60" />
            <h3 className="text-sm font-semibold text-slate-200">No PR Reviews Found</h3>
            <p className="text-xs text-[#787777] mt-1 mb-5">
              Submit a PR to your GitHub repository or trigger a live simulation review.
            </p>
            <button
              type="button"
              onClick={handleRunDemo}
              disabled={triggering}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition-colors cursor-pointer"
            >
              <Zap className="w-4 h-4 fill-current" />
              <span>{triggering ? "Analyzing..." : "Trigger Live PR Review"}</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#182130] text-[#787777] font-mono text-[11px] bg-[#101520]">
                  <th className="py-3 px-4 font-medium w-20">PR #</th>
                  <th className="py-3 px-4 font-medium">Title &amp; Branch</th>
                  <th className="py-3 px-4 font-medium w-36">Author</th>
                  <th className="py-3 px-4 font-medium w-28 text-center">Score</th>
                  <th className="py-3 px-4 font-medium w-32 text-center">Consensus</th>
                  <th className="py-3 px-4 font-medium w-24 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#182130]">
                {filteredPrs.map((pr) => {
                  const isApproved = pr.consensus.decision === "approved";
                  return (
                    <tr
                      key={pr.meta.id}
                      onClick={() => navigate(`/pull-requests/${pr.meta.id}`)}
                      className="hover:bg-[#192232]/80 transition-colors cursor-pointer group"
                    >
                      <td className="py-4 px-4 font-mono font-bold text-slate-200">
                        #{pr.meta.prNumber}
                      </td>

                      <td className="py-4 px-4">
                        <div className="font-semibold text-slate-100 text-sm group-hover:text-sky-300 transition-colors">
                          {pr.meta.title}
                        </div>
                        <div className="flex items-center gap-2 mt-1 font-mono text-[11px] text-[#787777]">
                          <span className="text-slate-300">{pr.meta.sourceBranch}</span>
                          <span>&rarr;</span>
                          <span>{pr.meta.targetBranch}</span>
                          <span>&bull;</span>
                          <span>{pr.meta.shortHash}</span>
                        </div>
                      </td>

                      <td className="py-4 px-4 font-medium text-slate-300">
                        @{pr.meta.author.username}
                      </td>

                      <td className="py-4 px-4 text-center font-mono">
                        <span className="text-sm font-bold text-slate-100">
                          {pr.consensus.score}
                        </span>
                        <span className="text-[#787777] text-[10px]"> / 100</span>
                      </td>

                      <td className="py-4 px-4 text-center">
                        <Badge
                          variant={isApproved ? "approved" : "rejected"}
                          className="text-[10px] px-2.5 py-0.5"
                        >
                          {pr.consensus.decision.toUpperCase()}
                        </Badge>
                      </td>

                      <td className="py-4 px-4 text-right">
                        <span className="inline-flex items-center gap-1 text-xs text-sky-400 font-medium group-hover:translate-x-1 transition-transform">
                          Review <ArrowRight className="w-3.5 h-3.5" />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
