import { Shield, CheckCircle2, Boxes, FlaskConical, Cpu, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useNavigation } from "@/context/NavigationContext";
import { cn } from "@/lib/utils";
import type { AgentScore } from "@/lib/api";

export interface AgentScoreCardProps {
  agent: AgentScore;
}

export function AgentScoreCard({ agent }: AgentScoreCardProps) {
  const { highlightedAgent, setHighlightedAgent } = useNavigation();
  const isHighlighted = highlightedAgent === agent.id;

  const getIcon = (iconName: string) => {
    switch (iconName.toLowerCase()) {
      case "shield":
        return <Shield className="w-4 h-4 text-slate-300 shrink-0" />;
      case "checkcircle":
      case "checkcircle2":
        return <CheckCircle2 className="w-4 h-4 text-slate-300 shrink-0" />;
      case "boxes":
        return <Boxes className="w-4 h-4 text-slate-300 shrink-0" />;
      case "flaskconical":
      case "flask":
        return <FlaskConical className="w-4 h-4 text-slate-300 shrink-0" />;
      case "cpu":
        return <Cpu className="w-4 h-4 text-slate-300 shrink-0" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-slate-300 shrink-0" />;
    }
  };

  // Compute progress bar fill percentage
  let progressPercent = 0;
  if (agent.scoreType === "pass-fail") {
    progressPercent = agent.status === "pass" ? 100 : 25;
  } else if (agent.score !== undefined) {
    progressPercent = (agent.score / 10) * 100;
  }

  return (
    <div
      onClick={() => setHighlightedAgent(isHighlighted ? null : agent.id)}
      className={cn(
        "bg-[#151C28] border rounded-xl p-4 flex flex-col justify-between transition-all select-none shadow-sm min-h-[145px] cursor-pointer",
        isHighlighted
          ? "border-slate-300 ring-1 ring-slate-300/40 bg-[#192233]"
          : "border-[#1e2738] hover:border-[#2d3a52]"
      )}
    >
      {/* Top Row: Icon + Name + Badge/Score */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 overflow-hidden">
          {getIcon(agent.icon)}
          <span className="text-xs font-semibold text-slate-100 truncate">
            {agent.agentName}
          </span>
        </div>

        {agent.scoreType === "pass-fail" ? (
          <Badge
            variant={agent.status === "pass" ? "pass" : "fail"}
            className="text-[10px] px-2 py-0.5"
          >
            {agent.status === "pass" ? "PASS" : "FAIL"}
          </Badge>
        ) : (
          <div className="flex items-baseline gap-0.5 font-mono">
            <span className="text-sm font-bold text-slate-100">
              {agent.score?.toFixed(1)}
            </span>
            <span className="text-[10px] text-[#787777]">/10</span>
          </div>
        )}
      </div>

      {/* Middle: Progress Bar */}
      <div className="my-2">
        <ProgressBar
          value={progressPercent}
          variant={
            agent.status === "fail"
              ? "danger"
              : progressPercent < 60
              ? "warning"
              : "default"
          }
          className="h-1 bg-[#101520]"
          barClassName={agent.status === "fail" ? "bg-red-400" : "bg-slate-200"}
        />
      </div>

      {/* Bottom Row: Weight + Summary */}
      <div className="mt-1 flex flex-col gap-0.5">
        <span className="text-[11px] font-mono text-[#787777]">
          Weight: {agent.weightPercent}%
        </span>
        <p className="text-xs text-slate-300 font-medium line-clamp-1">
          {agent.summary}
        </p>
      </div>
    </div>
  );
}

export function AgentScoreGrid({ agents }: { agents: AgentScore[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
      {agents.map((agent) => (
        <AgentScoreCard key={agent.id} agent={agent} />
      ))}
    </div>
  );
}
