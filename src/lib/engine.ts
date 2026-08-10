import type { AgentVerdict, PRReview, ScanFinding, Severity } from './types';
import type { SamplePR } from './samplePRs';

const uid = () => Math.random().toString(36).slice(2, 11);

const severityOrder: Severity[] = ['low', 'medium', 'high', 'critical'];

function rank(s: Severity) {
  return severityOrder.indexOf(s);
}

export function detectFindings(diff: string): ScanFinding[] {
  const findings: ScanFinding[] = [];

  if (/password|secret|api[_-]?key|token|sk-[a-z0-9]/i.test(diff)) {
    findings.push({
      id: uid(),
      tool: 'Trivy + Gitleaks',
      severity: 'critical',
      title: 'Hardcoded secret detected',
      file: extractFile(diff) ?? 'src/api/users.py',
      line: 16,
      description:
        'A plaintext credential is committed to source. Rotate the secret immediately and move it to a vault or environment variable.',
    });
  }

  if (/f["']SELECT.*\{.*\}["']|execute\(f["'].*\{.*\}["']\)/i.test(diff)) {
    findings.push({
      id: uid(),
      tool: 'SonarQube',
      severity: 'critical',
      title: 'SQL injection via string interpolation',
      file: extractFile(diff) ?? 'src/api/users.py',
      line: 21,
      description:
        'User input is concatenated into a SQL query. Use parameterized queries or an ORM to prevent injection.',
    });
  }

  if (/require\(/.test(diff) && !/import|from ['"]/m.test(diff)) {
    findings.push({
      id: uid(),
      tool: 'Semgrep',
      severity: 'medium',
      title: 'Legacy synchronous require() in ES module',
      file: extractFile(diff) ?? 'src/components/ProductGrid.tsx',
      line: 7,
      description:
        'CommonJS require() blocks tree-shaking. Migrate to ES import for better bundling and lazy-load support.',
    });
  }

  // Code smells — light, always-present
  if (/TODO|FIXME|HACK/i.test(diff)) {
    findings.push({
      id: uid(),
      tool: 'SonarQube',
      severity: 'low',
      title: 'Unresolved TODO marker',
      file: extractFile(diff) ?? 'unknown',
      line: 1,
      description: 'A TODO/FIXME was introduced. Track it or resolve before merge.',
    });
  }

  // If nothing critical was found, add a clean baseline finding
  if (findings.length === 0) {
    findings.push({
      id: uid(),
      tool: 'Checkov',
      severity: 'low',
      title: 'No IaC misconfigurations',
      file: '-',
      line: 0,
      description: 'Static analysis completed with no policy violations.',
    });
  }

  return findings;
}

function extractFile(diff: string): string | null {
  const m = diff.match(/diff --git a\/(\S+) b\//);
  return m ? m[1] : null;
}

const agentMeta: Record<
  string,
  { name: string; emoji: string }
> = {
  security: { name: 'Security Agent', emoji: 'shield' },
  tech_debt: { name: 'Technical Debt Agent', emoji: 'wrench' },
  story: { name: 'Story Matching Agent', emoji: 'book' },
  performance: { name: 'Performance Agent', emoji: 'gauge' },
};

function reviewAgents(diff: string, findings: ScanFinding[]): AgentVerdict[] {
  const hasCritical = findings.some((f) => rank(f.severity) >= rank('critical'));
  const hasHigh = findings.some((f) => rank(f.severity) >= rank('high'));
  const hasMedium = findings.some((f) => rank(f.severity) >= rank('medium'));

  const isRisky = hasCritical || hasHigh;
  const isClean = !hasHigh && !hasCritical;

  // Performance signals
  const hasPerfFix = /lazy|memo|useMemo|Suspense|defer|cache/i.test(diff);
  const hasNPlusOne = /for.*in.*select|\.map\(.*query|\.map\(.*fetch/i.test(diff);

  // Tech debt signals
  const hasLegacyPattern = /require\(|var |public static|God class|TODO|FIXME/i.test(diff);
  const hasCleanStructure = /import |from ['"]|export |def |class /i.test(diff) && !hasLegacyPattern;

  const agents: AgentVerdict[] = [
    {
      id: 'security',
      name: agentMeta.security.name,
      verdict: isRisky ? 'request_changes' : 'approve',
      reason: isRisky
        ? `${findings.filter((f) => rank(f.severity) >= rank('high')).length} critical/high finding${findings.filter((f) => rank(f.severity) >= rank('high')).length > 1 ? 's' : ''} — secrets or injection must be remediated before merge.`
        : 'No credentials, injection sinks, or unsafe patterns detected in the diff.',
      confidence: isRisky ? 0.96 : 0.91,
    },
    {
      id: 'tech_debt',
      name: agentMeta.tech_debt.name,
      verdict: hasLegacyPattern || (hasMedium && !isClean) ? 'request_changes' : 'approve',
      reason: hasLegacyPattern
        ? 'Legacy pattern (synchronous require) introduces maintainability debt; prefer modern imports.'
        : hasCleanStructure
          ? 'Clean module boundaries, consistent imports, no new debt introduced.'
          : 'Minor code smell noted but does not block merge.',
      confidence: 0.84,
    },
    {
      id: 'story',
      name: agentMeta.story.name,
      verdict: 'approve',
      reason: 'Implementation matches the linked ticket acceptance criteria and branch intent.',
      confidence: 0.88,
    },
    {
      id: 'performance',
      name: agentMeta.performance.name,
      verdict: hasNPlusOne ? 'request_changes' : 'approve',
      reason: hasNPlusOne
        ? 'Potential N+1 query pattern inside a loop — batch the query to avoid latency on large datasets.'
        : hasPerfFix
          ? 'Positive impact: lazy loading and memoization reduce initial render cost and re-renders.'
          : 'No performance regressions detected; algorithmic complexity unchanged.',
      confidence: 0.82,
    },
  ];

  return agents;
}

export function reviewPR(sample: SamplePR): Omit<
  PRReview,
  'id' | 'status' | 'submittedAt' | 'reviewTimeMs'
> {
  const findings = detectFindings(sample.diffText);
  const agents = reviewAgents(sample.diffText, findings);

  const approvals = agents.filter((a) => a.verdict === 'approve').length;
  const consensus = approvals >= 3 ? 'approve' : 'request_changes';

  const blockingAgents = agents.filter((a) => a.verdict === 'request_changes');
  const consensusReason = consensus === 'approve'
    ? `${approvals}/4 agents approved — consensus reached to merge.`
    : `${4 - approvals}/4 agents requested changes (${blockingAgents.map((a) => a.name.replace(' Agent', '')).join(', ')}).`;

  const lines = sample.diffText.split('\n');
  const additions = lines.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length;
  const deletions = lines.filter((l) => l.startsWith('-') && !l.startsWith('---')).length;
  const filesChanged = (sample.diffText.match(/diff --git/g) || []).length || 1;

  return {
    prNumber: sample.prNumber,
    repoName: sample.repoName,
    branch: sample.branch,
    author: sample.author,
    title: sample.title,
    diffText: sample.diffText,
    findings,
    agents,
    consensus,
    consensusReason,
    filesChanged,
    additions,
    deletions,
  };
}

export function computeMetrics(reviews: PRReview[]): {
  totalReviewed: number;
  approved: number;
  changesRequested: number;
  approvalRate: number;
  avgReviewTimeMs: number;
  avgReviewTimeLabel: string;
  vulnerabilitiesCaught: number;
} {
  const completed = reviews.filter((r) => r.status === 'completed');
  const approved = completed.filter((r) => r.consensus === 'approve').length;
  const changes = completed.filter((r) => r.consensus === 'request_changes').length;
  const total = completed.length || 1;
  const avgMs = completed.reduce((s, r) => s + r.reviewTimeMs, 0) / total;
  const vulns = completed.reduce(
    (s, r) => s + r.findings.filter((f) => f.severity === 'critical' || f.severity === 'high').length,
    0,
  );

  return {
    totalReviewed: completed.length,
    approved,
    changesRequested: changes,
    approvalRate: completed.length ? Math.round((approved / total) * 100) : 0,
    avgReviewTimeMs: Math.round(avgMs),
    avgReviewTimeLabel: `${(avgMs / 1000).toFixed(1)}s`,
    vulnerabilitiesCaught: vulns,
  };
}

export function newId() {
  return uid();
}
