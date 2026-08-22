import { CheckCircle2, XCircle, Clock, AlertTriangle } from "lucide-react";
import { Badge } from "@/lib/../components/ui/Badge";
import type { ConsensusScore, AgentScore } from "@/lib/api";

export interface ConsensusScoreCardProps {
  consensus: ConsensusScore;
  agents?: AgentScore[];
}

export const REASON_LABELS: Record<string, string> = {
  SCORE_BELOW_THRESHOLD: "Score below threshold (80)",
  CRITICAL_SECURITY_ISSUES: "Critical security vulnerabilities detected",
  SECURITY_FAILED: "Security audit failed",
  QA_TESTS_FAILED: "QA test suite / regression checks failed",
  QA_FAILED: "QA test suite / regression checks failed",
  LOW_COVERAGE: "Test coverage below minimum threshold",
  TECH_DEBT_HIGH: "Technical debt & code quality issues",
  PERFORMANCE_DEGRADATION: "Performance regression / high complexity",
  STORY_MISMATCH: "Requirement specifications mismatch",
  BRANCH_CHECKS_FAILED: "Branch status checks failed",
  REVIEW_POST_FAILED: "GitHub review post failed",
};

export function formatBlockingReason(reason?: string): string {
  if (!reason || typeof reason !== "string") return "Review criteria not met";
  return REASON_LABELS[reason] || reason.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
}

export function ConsensusScoreCard({ consensus }: ConsensusScoreCardProps) {
  const score = typeof consensus?.score === "number" ? consensus.score : 0;
  const decision = typeof consensus?.decision === "string" ? consensus.decision : "pending";
  const gates = consensus?.gates ?? { security: "pending", qa: "pending", evidence: "pending" };

  const isRejected = decision === "rejected" || decision === "blocked";

  // Defensive extraction of blocking reasons with full optional chaining
  const rawReasons: string[] = Array.isArray((consensus as any)?.blocking_reasons)
    ? (consensus as any).blocking_reasons
    : Array.isArray((consensus as any)?.blockingReasons)
    ? (consensus as any).blockingReasons
    : [];

  const formattedReasons: string[] = rawReasons
    .map((r) => formatBlockingReason(r))
    .filter((r): r is string => Boolean(r && r.trim()));

  // Fallback if rejected but reasons array is empty
  if (isRejected && formattedReasons.length === 0) {
    if (score < 80) {
      formattedReasons.push("Score below threshold (80)");
    } else {
      formattedReasons.push("Review requirements not met");
    }
  }

  // Circular gauge parameters
  const size = 180;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.82;
  const strokeDashoffset = arcLength - (arcLength * Math.min(Math.max(score, 0), 100)) / 100;

  const getGateStatus = (status?: string) => {
    switch (status) {
      case "passed":
      case "verified":
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
          text: status === "verified" ? "Verified" : "Passed",
        };
      case "failed":
      case "unverified":
        return {
          icon: <XCircle className="w-4 h-4 text-red-400" />,
          text: status === "unverified" ? "Unverified" : "Failed",
        };
      case "unknown":
      case "incomplete":
        return {
          icon: <XCircle className="w-4 h-4 text-amber-400" />,
          text: status === "incomplete" ? "Incomplete" : "Unavailable",
        };
      case "pending":
      default:
        return {
          icon: <Clock className="w-4 h-4 text-yellow-400" />,
          text: "Pending",
        };
    }
  };

  const securityStatus = getGateStatus(gates?.security);
  const qaStatus = getGateStatus(gates?.qa);
  const evidenceStatus = getGateStatus(gates?.evidence);

  return (
    <div className="w-full bg-[#151C28] border border-[#1e2738] rounded-2xl p-6 mb-5 shadow-lg shadow-black/20 select-none">
      <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
        {/* Left: Custom SVG Circular Progress Ring */}
        <div className="relative flex items-center justify-center shrink-0">
          {/* Subtle Ambient Radial Glow */}
          <div className="absolute inset-0 bg-slate-400/5 blur-2xl rounded-full pointer-events-none" />

          <svg
            width={size}
            height={size}
            className="transform rotate-[122deg] overflow-visible"
          >
            {/* Background Track Arc */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="#1b2333"
              strokeWidth={strokeWidth}
              strokeDasharray={`${arcLength} ${circumference}`}
              strokeLinecap="round"
            />
            {/* Filled Progress Arc */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="#f1f5f9"
              strokeWidth={strokeWidth}
              strokeDasharray={`${arcLength} ${circumference}`}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          {/* Centered Score Display */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-5xl font-light tracking-tight text-white font-headline leading-none">
              {score}
            </span>
            <span className="text-xs font-mono text-[#787777] tracking-wider mt-1.5">
              / 100
            </span>
          </div>
        </div>

        {/* Right Section: Decision Headline + Sub-cells */}
        <div className="flex-1 w-full flex flex-col justify-between min-h-[140px]">
          {/* Header Row */}
          <div className="flex items-center justify-between pb-4">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-headline">
              Consensus Decision
            </h2>
            <Badge
              variant={
                decision === "approved"
                  ? "approved"
                  : isRejected
                  ? "rejected"
                  : "pending"
              }
              className="text-xs px-3.5 py-1"
            >
              {(decision || "PENDING").toUpperCase()}
            </Badge>
          </div>

          {/* Sub-cells Grid (Security Gate, QA Gate, Evidence) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Security Gate */}
            <div className="bg-[#101520] border border-[#1a2333] rounded-xl p-3.5 flex flex-col gap-1.5 transition-colors hover:border-[#222d42]">
              <span className="text-[11px] font-medium text-[#787777] font-mono tracking-wide">
                Security Gate
              </span>
              <div className="flex items-center gap-2">
                {securityStatus.icon}
                <span className="text-sm font-semibold text-slate-100">
                  {securityStatus.text}
                </span>
              </div>
            </div>

            {/* QA Gate */}
            <div className="bg-[#101520] border border-[#1a2333] rounded-xl p-3.5 flex flex-col gap-1.5 transition-colors hover:border-[#222d42]">
              <span className="text-[11px] font-medium text-[#787777] font-mono tracking-wide">
                QA Gate
              </span>
              <div className="flex items-center gap-2">
                {qaStatus.icon}
                <span className="text-sm font-semibold text-slate-100">
                  {qaStatus.text}
                </span>
              </div>
            </div>

            {/* Evidence */}
            <div className="bg-[#101520] border border-[#1a2333] rounded-xl p-3.5 flex flex-col gap-1.5 transition-colors hover:border-[#222d42]">
              <span className="text-[11px] font-medium text-[#787777] font-mono tracking-wide">
                Evidence
              </span>
              <div className="flex items-center gap-2">
                {evidenceStatus.icon}
                <span className="text-sm font-semibold text-slate-100">
                  {evidenceStatus.text}
                </span>
              </div>
            </div>
          </div>

          {/* Rejection / Blocking Reasons Box */}
          {isRejected && formattedReasons.length > 0 && (
            <div className="mt-3.5 pt-3 border-t border-rose-500/20 flex flex-col gap-1.5">
              <div className="flex items-center gap-1.5 text-[11px] font-mono font-bold text-rose-400 uppercase tracking-wider">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                <span>Rejection Reason{formattedReasons.length > 1 ? "s" : ""}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {formattedReasons.map((reason, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2 py-0.5 rounded bg-rose-950/40 border border-rose-500/30 text-rose-200"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0" />
                    {reason}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

