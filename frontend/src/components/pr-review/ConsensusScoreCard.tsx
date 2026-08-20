import { CheckCircle2, XCircle, Clock } from "lucide-react";
import { Badge } from "@/lib/../components/ui/Badge";
import type { ConsensusScore } from "@/lib/api";

export interface ConsensusScoreCardProps {
  consensus: ConsensusScore;
}

export function ConsensusScoreCard({ consensus }: ConsensusScoreCardProps) {
  const { score, decision, gates } = consensus;

  // Circular gauge parameters
  const size = 180;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  // Let the circle arc span approx 280-300 degrees or standard full circle with gap at bottom
  // Looking at the screenshot, it's an open arc at the bottom (~280 degrees)
  const arcLength = circumference * 0.82;
  const strokeDashoffset = arcLength - (arcLength * Math.min(score, 100)) / 100;

  const getGateStatus = (status: "passed" | "failed" | "pending" | "verified" | "unverified") => {
    switch (status) {
      case "passed":
      case "verified":
        return {
          icon: <CheckCircle2 className="w-4 h-4 text-slate-200" />,
          text: status === "verified" ? "Verified" : "Passed",
        };
      case "failed":
      case "unverified":
        return {
          icon: <XCircle className="w-4 h-4 text-red-400" />,
          text: status === "unverified" ? "Unverified" : "Failed",
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
          <div className="flex items-center justify-between pb-6">
            <h2 className="text-2xl font-bold tracking-tight text-slate-100 font-headline">
              Consensus Decision
            </h2>
            <Badge
              variant={
                decision === "approved"
                  ? "approved"
                  : decision === "rejected"
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
        </div>
      </div>
    </div>
  );
}
