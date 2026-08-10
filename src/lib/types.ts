export type Verdict = 'approve' | 'request_changes';

export type AgentId = 'security' | 'tech_debt' | 'story' | 'performance';

export interface AgentVerdict {
  id: AgentId;
  name: string;
  verdict: Verdict;
  reason: string;
  confidence: number;
}

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface ScanFinding {
  id: string;
  tool: string;
  severity: Severity;
  title: string;
  file: string;
  line: number;
  description: string;
}

export type PRStatus = 'queued' | 'scanning' | 'reviewing' | 'consensus' | 'completed';

export interface PRReview {
  id: string;
  prNumber: number;
  repoName: string;
  branch: string;
  author: string;
  title: string;
  diffText: string;
  status: PRStatus;
  submittedAt: number;
  reviewTimeMs: number;
  findings: ScanFinding[];
  agents: AgentVerdict[];
  consensus: Verdict;
  consensusReason: string;
  filesChanged: number;
  additions: number;
  deletions: number;
}

export interface Metrics {
  totalReviewed: number;
  approved: number;
  changesRequested: number;
  approvalRate: number;
  avgReviewTimeMs: number;
  avgReviewTimeLabel: string;
  vulnerabilitiesCaught: number;
}
