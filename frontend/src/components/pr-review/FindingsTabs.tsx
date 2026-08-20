import { Badge } from "@/components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { QATestTab } from "@/components/pr-review/QATestTab";
import { DiffInspectorTab } from "@/components/pr-review/DiffInspectorTab";
import { SystemArchTab } from "@/components/pr-review/SystemArchTab";
import { useNavigation } from "@/context/NavigationContext";
import type { PullRequestReview, Finding } from "@/lib/api";

export interface FindingsTabsProps {
  pr: PullRequestReview;
}

export function FindingsTabs({ pr }: { pr: PullRequestReview }) {
  const { activeFindingsTab, setActiveFindingsTab } = useNavigation();

  // Calculate severity counts
  const criticalCount = pr.findings.filter((f) => f.severity === "critical").length;
  const highCount = pr.findings.filter((f) => f.severity === "high").length;
  const medCount = pr.findings.filter((f) => f.severity === "medium").length;

  return (
    <div id="section-findings" className="w-full bg-[#151C28] border border-[#1e2738] rounded-2xl p-5 select-none shadow-sm">
      <Tabs value={activeFindingsTab} onValueChange={setActiveFindingsTab}>
        {/* Tab Headers Strip */}
        <TabsList className="mb-5">
          <TabsTrigger value="security">Security &amp; Vulnerability</TabsTrigger>
          <TabsTrigger value="qa">QA &amp; Test</TabsTrigger>
          <TabsTrigger value="diff">Diff Inspector</TabsTrigger>
          <TabsTrigger value="arch">System Arch</TabsTrigger>
        </TabsList>

        {/* Tab 1: Security & Vulnerability */}
        <TabsContent value="security">
          {/* Stat Severity Pills/Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mb-5 max-w-xl">
            {/* Critical Stat */}
            <div className="bg-[#1c0d11] border border-[#7A1F2B] rounded-lg px-4 py-2.5 flex items-center gap-3">
              <span className="text-2xl font-bold text-slate-100 font-headline">
                {criticalCount}
              </span>
              <span className="text-xs font-mono font-medium text-[#f87171]">
                Critical
              </span>
            </div>

            {/* High Stat */}
            <div className="bg-[#27170c] border border-[#C77A2B] rounded-lg px-4 py-2.5 flex items-center gap-3">
              <span className="text-2xl font-bold text-[#fb923c] font-headline">
                {highCount}
              </span>
              <span className="text-xs font-mono font-medium text-[#fb923c]">
                High
              </span>
            </div>

            {/* Medium Stat */}
            <div className="bg-[#221b0a] border border-[#C9A227] rounded-lg px-4 py-2.5 flex items-center gap-3">
              <span className="text-2xl font-bold text-[#facc15] font-headline">
                {medCount}
              </span>
              <span className="text-xs font-mono font-medium text-[#facc15]">
                Medium
              </span>
            </div>
          </div>

          {/* Findings Table */}
          <div className="bg-[#101520] border border-[#1e2738] rounded-xl overflow-hidden shadow-inner">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#182130] text-[#787777] font-mono text-[11px]">
                    <th className="py-3 px-4 font-medium w-28">Severity</th>
                    <th className="py-3 px-4 font-medium w-36">Tool</th>
                    <th className="py-3 px-4 font-medium w-48">Rule ID</th>
                    <th className="py-3 px-4 font-medium">File</th>
                    <th className="py-3 px-4 font-medium text-right w-20">Line</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#151c2a]">
                  {pr.findings.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-[#787777] font-mono">
                        No security vulnerabilities or policy violations detected.
                      </td>
                    </tr>
                  ) : (
                    pr.findings.map((f: Finding) => {
                      const sev = f.severity.toUpperCase();
                      const isHigh = f.severity === "high";
                      const isCritical = f.severity === "critical";
                      const isMed = f.severity === "medium" || f.severity === "low";

                      return (
                        <tr
                          key={f.id}
                          className="hover:bg-[#151d2c]/60 transition-colors group"
                        >
                          {/* Severity Badge */}
                          <td className="py-3.5 px-4">
                            <Badge
                              variant={
                                isCritical
                                  ? "critical"
                                  : isHigh
                                  ? "high"
                                  : isMed
                                  ? "med"
                                  : "default"
                              }
                              className="w-14 justify-center"
                            >
                              {isMed && sev === "MEDIUM" ? "MED" : sev}
                            </Badge>
                          </td>

                          {/* Tool Name */}
                          <td className="py-3.5 px-4 font-medium text-slate-200">
                            {f.tool}
                          </td>

                          {/* Rule ID */}
                          <td className="py-3.5 px-4 font-mono text-slate-300 font-medium">
                            {f.ruleId}
                          </td>

                          {/* File Path Pill Tag */}
                          <td className="py-3.5 px-4">
                            <span className="inline-block bg-[#121824] border border-[#1d273a] px-2.5 py-1 rounded text-slate-200 font-mono text-xs max-w-xs sm:max-w-sm md:max-w-md truncate">
                              {f.file}
                            </span>
                          </td>

                          {/* Line Number */}
                          <td className="py-3.5 px-4 font-mono text-[#8e9bb0] text-right font-medium">
                            {f.line}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>

        {/* Tab 2: QA & Test */}
        <TabsContent value="qa">
          <QATestTab pr={pr} />
        </TabsContent>

        {/* Tab 3: Diff Inspector */}
        <TabsContent value="diff">
          <DiffInspectorTab pr={pr} />
        </TabsContent>

        {/* Tab 4: System Arch */}
        <TabsContent value="arch">
          <SystemArchTab pr={pr} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
