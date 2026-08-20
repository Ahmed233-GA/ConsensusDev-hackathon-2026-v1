import { Shield, CheckCircle2, Boxes, FlaskConical } from "lucide-react";
import { ProgressBar } from "@/components/ui/ProgressBar";

export function AgentsPage() {
  const agents = [
    {
      name: "Security Auditor",
      role: "DevSecOps & SAST Scanner",
      icon: Shield,
      weight: 40,
      model: "Checkov + Trivy + SonarQube",
      strictness: "Blocking (Zero critical CVEs)",
      description: "Detects secrets, infrastructure-as-code misconfigurations, dependency vulnerabilities, and SQLi risks.",
      rulesEvaluated: 148,
      status: "Active",
    },
    {
      name: "Code Quality Reviewer",
      role: "Technical Debt & Style Guard",
      icon: CheckCircle2,
      weight: 20,
      model: "GPT-4o Mini",
      strictness: "Advisory (Cognitive complexity < 10)",
      description: "Ensures PEP8 adherence, typing completeness, cyclomatic complexity bounds, and clean code hygiene.",
      rulesEvaluated: 32,
      status: "Active",
    },
    {
      name: "Architecture Evaluator",
      role: "Modular Boundaries & Topology Guard",
      icon: Boxes,
      weight: 20,
      model: "GPT-4o Mini",
      strictness: "Blocking (Zero circular imports)",
      description: "Enforces microservice domain boundaries, idempotency on webhook handlers, and clean API contracts.",
      rulesEvaluated: 18,
      status: "Active",
    },
    {
      name: "QA & Mutation Guard",
      role: "Test Execution & Coverage Gate",
      icon: FlaskConical,
      weight: 20,
      model: "Shahd QA Runner (Pytest + Mutmut)",
      strictness: "Blocking (Pass rate 100%, Coverage >= 80%)",
      description: "Runs full test suite in sandboxed runner, calculates mutation kill score, and checks regressions.",
      rulesEvaluated: 24,
      status: "Active",
    },
  ];

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
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent) => {
          const Icon = agent.icon;
          return (
            <div
              key={agent.name}
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
                    Weight: {agent.weight}%
                  </span>
                </div>

                <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                  {agent.description}
                </p>

                <div className="bg-[#101520] border border-[#1a2333] rounded-xl p-3 flex flex-col gap-2 text-xs font-mono mb-4">
                  <div className="flex justify-between">
                    <span className="text-[#787777]">Engine / Model:</span>
                    <span className="text-slate-200">{agent.model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#787777]">Policy Threshold:</span>
                    <span className="text-emerald-400 font-semibold">{agent.strictness}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#787777]">Active Rules:</span>
                    <span className="text-slate-300">{agent.rulesEvaluated} rules</span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] font-mono text-[#787777] mb-1">
                  <span>Consensus Vote Weight</span>
                  <span className="text-slate-200">{agent.weight}%</span>
                </div>
                <ProgressBar value={agent.weight * 2.5} className="h-1 bg-[#101520]" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
