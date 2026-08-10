import { AlertTriangle, Bug, ShieldAlert, CheckCircle2, ChevronRight } from 'lucide-react';
import type { ScanFinding, Severity } from '@/lib/types';

const severityStyle: Record<Severity, { label: string; color: string; bg: string; border: string }> = {
  critical: {
    label: 'CRITICAL',
    color: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
  },
  high: {
    label: 'HIGH',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
  },
  medium: {
    label: 'MEDIUM',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
  },
  low: {
    label: 'LOW',
    color: 'text-teal-400',
    bg: 'bg-teal-500/10',
    border: 'border-teal-500/30',
  },
};

function findingIcon(severity: Severity) {
  if (severity === 'critical' || severity === 'high') return ShieldAlert;
  if (severity === 'medium') return Bug;
  if (severity === 'low') return AlertTriangle;
  return AlertTriangle;
}

interface FindingsPanelProps {
  findings: ScanFinding[];
  title?: string;
}

export function FindingsPanel({ findings, title = 'Static Analysis Findings' }: FindingsPanelProps) {
  const realFindings = findings.filter(
    (f) => f.severity !== 'low' || f.title !== 'No IaC misconfigurations',
  );
  const hasIssues = realFindings.length > 0;

  return (
    <div className="glass rounded-2xl border border-ink-700/70 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-ink-700/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-amber-400" />
          <h3 className="text-[13px] font-semibold text-white">{title}</h3>
        </div>
        <span className="text-[10px] text-ink-300 font-mono">
          SonarQube · Trivy · Checkov · Semgrep
        </span>
      </div>

      <div className="divide-y divide-ink-800/80">
        {!hasIssues && (
          <div className="px-5 py-6 flex items-center gap-3 text-teal-400">
            <CheckCircle2 className="w-5 h-5" />
            <div>
              <p className="text-sm font-semibold">Clean scan — no issues found</p>
              <p className="text-[11px] text-ink-300">
                All static analysis tools passed with zero violations.
              </p>
            </div>
          </div>
        )}

        {realFindings.map((f, i) => {
          const s = severityStyle[f.severity];
          const Icon = findingIcon(f.severity);
          return (
            <div
              key={f.id}
              className="px-5 py-3.5 flex items-start gap-3 hover:bg-ink-800/40 transition-colors animate-fade-up"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div
                className={`w-8 h-8 rounded-lg ${s.bg} ${s.border} border flex items-center justify-center ${s.color} flex-shrink-0`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[9.5px] font-bold px-1.5 py-0.5 rounded ${s.bg} ${s.color} uppercase tracking-wider`}
                  >
                    {s.label}
                  </span>
                  <span className="text-[13px] font-semibold text-white">{f.title}</span>
                </div>
                <p className="text-[11.5px] text-ink-200 mt-1 leading-relaxed">{f.description}</p>
                <div className="flex items-center gap-3 mt-1.5 text-[10px] text-ink-300 font-mono">
                  <span>{f.tool}</span>
                  <ChevronRight className="w-3 h-3" />
                  <span>{f.file}</span>
                  {f.line > 0 && (
                    <>
                      <ChevronRight className="w-3 h-3" />
                      <span>:{f.line}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
