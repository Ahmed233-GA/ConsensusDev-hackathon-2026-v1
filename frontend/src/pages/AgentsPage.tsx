import * as React from "react";
import { Shield, CheckCircle2, Boxes, Cpu, RefreshCw } from "lucide-react";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { getAgentsInfo, type AgentInfo } from "@/lib/api";

export function AgentsPage() {
  const [agents, setAgents] = React.useState<AgentInfo[]>([]);
  const [loading, setLoading] = React.useState(true);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAgentsInfo();
      setAgents(data);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const getIcon = (agentId: string) => {
    switch (agentId.toLowerCase()) {
      case "security":
        return Shield;
      case "tech_debt":
        return CheckCircle2;
      case "story_match":
        return Boxes;
      case "performance":
      default:
        return Cpu;
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      <div className="flex items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-headline">
            Reviewer Agent Architecture &amp; Weights
          </h1>
          <p className="text-xs text-[#787777] mt-1">
            Configure agent consensus weights, model endpoints, and blocking thresholds.
          </p>
        </div>

        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#151C28] border border-[#1e2738] text-xs text-slate-300 hover:text-white"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent) => {
          const Icon = getIcon(agent.id);
          return (
            <div
              key={agent.id}
              className="bg-[#151C28] border border-[#1e2738] rounded-2xl p-5 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#101520] border border-[#1d273a] flex items-center justify-center text-slate-200">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-100">
                        {agent.name}
                      </h3>
                      <span className="text-[11px] text-[#787777] font-mono">
                        {agent.role}
                      </span>
                    </div>
                  </div>

                  <span className="text-xs font-mono font-bold text-sky-400 bg-sky-950/40 border border-sky-800/30 px-2 py-0.5 rounded">
                    Weight: {agent.weightPercent}%
                  </span>
                </div>

                <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                  {agent.description}
                </p>

                <div className="bg-[#101520] border border-[#1a2333] rounded-xl p-3 flex flex-col gap-2 text-xs font-mono mb-4">
                  <div className="flex justify-between">
                    <span className="text-[#787777]">Engine / Model:</span>
                    <span className="text-slate-200 truncate max-w-xs">{agent.model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#787777]">Policy Threshold:</span>
                    <span className="text-emerald-400 font-semibold">{agent.strictness}</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] font-mono text-[#787777] mb-1">
                  <span>Consensus Vote Weight</span>
                  <span className="text-slate-200">{agent.weightPercent}%</span>
                </div>
                <ProgressBar value={agent.weightPercent * 2.5} className="h-1 bg-[#101520]" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
