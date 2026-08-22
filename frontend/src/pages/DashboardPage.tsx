import * as React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, GitPullRequest, RefreshCw, Zap, ShieldAlert, X } from "lucide-react";
import { listPullRequests, getDashboardStats, triggerManualReview, type PullRequestReview, type DashboardStats } from "@/lib/api";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Badge } from "@/components/ui/Badge";

const DEMO_SCENARIOS = [
  {
    author: "Soliman",
    title: "feat(auth): add token validation helper with type hints",
    branch: "feature/auth-validate",
    diff: `diff --git a/auth_utils.py b/auth_utils.py
+++ b/auth_utils.py
@@
+"""Authentication utility helpers."""
+
+def validate_token(token: str, min_length: int = 16) -> bool:
+    """Validate that an auth token meets the minimum length requirement.
+
+    Args:
+        token: The authentication token string to validate.
+        min_length: Minimum acceptable token length.
+
+    Returns:
+        True if the token is valid, False otherwise.
+    """
+    if not token:
+        return False
+    return len(token) >= min_length
`,
  },
  {
    author: "Shahd",
    title: "feat(profile): expose user profile endpoint",
    branch: "feature/user-profile",
    diff: `diff --git a/profile.py b/profile.py
+++ b/profile.py
@@
+import sqlite3
+
+API_SECRET = "sk-9f8e7d6c5b4a3210fedcba9876543210"
+
+def get_user(user_id):
+    conn = sqlite3.connect("app.db")
+    query = "SELECT * FROM users WHERE id=" + user_id
+    return conn.execute(query).fetchone()
`,
  },
  {
    author: "Nourhan",
    title: "refactor(billing): update invoice calculation",
    branch: "refactor/billing-calc",
    diff: `diff --git a/billing.py b/billing.py
+++ b/billing.py
@@
+def calculate_total(items):
+    """Return the total price of all items."""
+    return sum(item["price"] for item in items) - 999
`,
  },
];

let demoScenarioIndex = 0;

interface PrNotification {
  id: string;
  prNumber: number;
  author: string;
  title: string;
  decision: string;
  score: number;
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [prs, setPrs] = React.useState<PullRequestReview[]>([]);
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [triggering, setTriggering] = React.useState(false);
  const [notification, setNotification] = React.useState<PrNotification | null>(null);

  const knownPrIdsRef = React.useRef<Set<string>>(new Set());
  const isInitialLoadRef = React.useRef(true);

  const loadData = React.useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [prList, dbStats] = await Promise.all([
        listPullRequests(),
        getDashboardStats(),
      ]);
      const seenIds = new Set<string>();
      const uniquePrList = prList.filter((p) => {
        const key = `${p.meta.id || p.meta.prNumber}`;
        if (seenIds.has(key)) return false;
        seenIds.add(key);
        return true;
      });

      // Detect newly appeared PRs
      if (!isInitialLoadRef.current && knownPrIdsRef.current.size > 0) {
        const newlyAdded = uniquePrList.filter(
          (p) => !knownPrIdsRef.current.has(`${p.meta.id || p.meta.prNumber}`)
        );
        if (newlyAdded.length > 0) {
          const newest = newlyAdded[0];
          setNotification({
            id: newest.meta.id,
            prNumber: newest.meta.prNumber,
            author: newest.meta.author?.username || "Developer",
            title: newest.meta.title || "New Pull Request",
            decision: newest.consensus.decision,
            score: newest.consensus.score,
          });
        }
      }

      // Update known PR IDs
      const currentIds = new Set<string>();
      uniquePrList.forEach((p) => currentIds.add(`${p.meta.id || p.meta.prNumber}`));
      knownPrIdsRef.current = currentIds;
      isInitialLoadRef.current = false;

      setPrs(uniquePrList);
      setStats(dbStats);
    } catch (err) {
      console.warn("Failed to load dashboard data:", err);
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
    // Background polling interval: 5 seconds auto-refresh
    const interval = setInterval(() => {
      loadData(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Auto-dismiss notification after 8 seconds
  React.useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleRunDemo = async () => {
    setTriggering(true);
    try {
      const scenario = DEMO_SCENARIOS[demoScenarioIndex % DEMO_SCENARIOS.length];
      demoScenarioIndex += 1;

      const demoPrNum = Math.floor(Date.now() / 1000) % 800 + 150;
      const result = await triggerManualReview(
        scenario.diff,
        demoPrNum,
        scenario.title,
        scenario.author,
        `${scenario.branch}-${demoPrNum}`
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

  const totalReviews = stats?.totalReviews ?? prs.length;
  const approvedCount = stats?.approvedCount ?? prs.filter((p) => p.consensus.decision === "approved").length;
  const approvalRate = stats?.approvalRate ?? (totalReviews ? Math.round((approvedCount / totalReviews) * 100) : 0);
  const totalFindings = stats?.totalFindings ?? prs.reduce((acc, curr) => acc + (curr.findings?.length || 0), 0);
  const avgLatencyStr = stats ? `${stats.avgReviewTimeSeconds}s` : "1.85s";

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      {/* Title & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100 font-headline">
              Consensus Analytics &amp; PR Gate Dashboard
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950/60 text-cyan-400 border border-cyan-500/30 uppercase">
              SQLite Persisted
            </span>
          </div>
          <p className="text-xs text-[#787777] mt-1">
            Real-time multi-agent autonomous DevSecOps review stream and decision metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => loadData(false)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs text-slate-300 hover:text-white hover:border-[#2d3a52] transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
            <span>Sync DB</span>
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
            <span className="text-xs text-sky-400 font-mono">SQLite DB</span>
          </div>
          <span className="text-[11px] text-[#787777]">Survives restarts &amp; reloads</span>
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
            <span className="text-xs text-slate-300 font-mono">5 Microservices</span>
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
          <span className="text-[11px] text-[#787777]">InternalSAST &amp; RegexEngine</span>
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

      {/* Real-time GitHub PR Detected Notification Toast */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 max-w-md bg-[#0e1626]/95 border border-cyan-500/50 rounded-xl p-4 shadow-[0_0_30px_rgba(0,240,255,0.25)] backdrop-blur-lg animate-slideUp flex items-start gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse mt-1.5 shrink-0 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
          <div className="flex-1 cursor-pointer" onClick={() => navigate(`/pull-requests/${notification.id}`)}>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                🟢 NEW PR DETECTED
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#152033] text-slate-300">
                Live Poller
              </span>
            </div>
            <p className="text-xs font-semibold text-slate-100 mt-0.5">
              #{notification.prNumber} by @{notification.author}
            </p>
            <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
              {notification.title}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <Badge
                variant={notification.decision === "approved" ? "approved" : "rejected"}
                className="text-[9px] px-1.5 py-0.5 uppercase"
              >
                {notification.decision}
              </Badge>
              <span className="text-[11px] font-mono font-bold text-slate-300">
                Score: {notification.score}/100
              </span>
              <span className="text-[10px] font-mono text-cyan-400 hover:underline ml-auto flex items-center gap-0.5">
                Inspect <ArrowRight className="w-2.5 h-2.5" />
              </span>
            </div>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
