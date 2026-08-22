import { CheckCircle2, XCircle, Clock, AlertOctagon, Info } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import type { ConsensusScore, AgentScore } from "@/lib/api";

export interface ConsensusScoreCardProps {
  consensus: ConsensusScore;
  agents?: AgentScore[];
}

export const BLOCKING_REASON_LABELS: Record<string, string> = {
  SCORE_BELOW_THRESHOLD: "Score below threshold (80)",
  STORY_REQUIREMENTS_NOT_MET: "Requirements / user story not met",
  TEST_FAILURE: "QA tests failed",
  CRITICAL_SECURITY_ISSUE: "Critical security vulnerability",
  CRITICAL_VULNERABILITY: "Critical security vulnerability",
  SECURITY_EVIDENCE_UNAVAILABLE: "Security evidence unavailable",
  QA_EVIDENCE_UNAVAILABLE: "QA evidence unavailable",
  SECURITY_GATE_FAILED: "Security gate failed",
  QA_GATE_FAILED: "QA gate failed",
  EVIDENCE_INCOMPLETE: "Evidence incomplete",
};

export function formatBlockingReason(reason: string): string {
  if (BLOCKING_REASON_LABELS[reason]) {
    return BLOCKING_REASON_LABELS[reason];
  }
  return reason
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ConsensusScoreCard({ consensus, agents }: ConsensusScoreCardProps) {
  const { score, decision, gates, blocking_reasons } = consensus;
  const isRejected = decision === "rejected" || decision === "blocked";

  // Compute friendly rejection reasons
  const reasonsList: string[] = [];
  if (blocking_reasons && blocking_reasons.length > 0) {
    blocking_reasons.forEach((r) => {
      const label = formatBlockingReason(r);
      if (!reasonsList.includes(label)) {
        reasonsList.push(label);
      }
    });
  } else if (isRejected) {
    if (score < 80) {
      reasonsList.push("Score below threshold (80)");
    }
    if (agents && agents.length > 0) {
      agents.forEach((a) => {
        if (a.status === "fail") {
          reasonsList.push(`${a.agentName} failed`);
        } else if (a.score !== undefined && a.score < 7.5) {
          reasonsList.push(`${a.agentName} low score (${a.score}/10)`);
        }
      });
    }
    if (reasonsList.length === 0) {
      reasonsList.push("Consensus quality threshold not met");
    }
  }

  // Circular gauge parameters
  const size = 180;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.82;
  const strokeDashoffset = arcLength - (arcLength * Math.min(score, 100)) / 100;

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

  const securityStatus = getGateStatus(gates.security);
  const qaStatus = getGateStatus(gates.qa);
  const evidenceStatus = getGateStatus(gates.evidence);

  return (
    <div className="w-full bg-[#151C28] border border-[#1e2738] rounded-2xl p-6 mb-5 shadow-lg shadow-black/20 select-none">
      <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
        {/* Left: Custom SVG Circular Progress Ring */}
        <div className="relative flex items-center justify-center shrink-0">
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
              stroke={isRejected ? "#f87171" : "#34d399"}
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

        {/* Right Section: Decision Headline + Sub-cells + Rejection Breakdown */}
        <div className="flex-1 w-full flex flex-col justify-between min-h-[140px]">
          {/* Header Row */}
          <div className="flex items-center justify-between pb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-headline">
                Consensus Decision
              </h2>
              {isRejected && score < 80 && (
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-red-950/80 border border-red-500/40 text-red-300">
                  Score {score}/100 &lt; Threshold 80
                </span>
              )}
            </div>
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
              {decision.toUpperCase()}
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

          {/* Explicit Rejection Reason Box */}
          {isRejected && (
            <div className="mt-4 p-3.5 rounded-xl bg-red-950/40 border border-red-500/30 text-xs flex flex-col gap-2 shadow-inner">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-red-400 font-semibold font-mono tracking-wide uppercase text-[11px]">
                  <AlertOctagon className="w-3.5 h-3.5 text-red-400 shrink-0" />
                  <span>Rejected Because:</span>
                </div>
                <span className="text-[10px] font-mono text-red-300/80">
                  Threshold: 80 / 100
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {reasonsList.map((reason, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md bg-red-900/60 border border-red-500/40 text-red-200 font-medium text-xs flex items-center gap-1.5"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                    {reason}
                  </span>
                ))}
              </div>

              <div className="text-[11px] text-slate-400 flex items-start gap-1.5 mt-0.5 font-sans leading-relaxed">
                <Info className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  {gates.security === "passed" && gates.qa === "passed" ? (
                    <>
                      All deterministic security &amp; QA gates <strong>passed</strong>, but autonomous multi-agent consensus scored <strong className="text-slate-200">{score}/100</strong> (below the 80 threshold). The rejection was driven by AI code quality or story requirement findings.
                    </>
                  ) : (
                    <>
                      Review blocked by one or more quality, story, or security guardrails.
                    </>
                  )}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
