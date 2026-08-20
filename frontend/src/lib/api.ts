export interface ConsensusScore {
  score: number; // 0-100
  decision: "approved" | "rejected" | "pending" | "blocked";
  gates: {
    security: "passed" | "failed" | "pending" | "unknown";
    qa: "passed" | "failed" | "pending" | "unknown";
    evidence: "verified" | "unverified" | "pending" | "incomplete";
  };
  summary?: string;
  blocking_reasons?: string[];
}

export interface AgentScore {
  id: string;
  agentName: string;
  icon: string; // lucide icon key name
  scoreType: "pass-fail" | "numeric";
  status?: "pass" | "fail";
  score?: number; // 0-10
  weightPercent: number;
  summary: string;
  details?: string[];
  confidence?: number;
}

export interface Finding {
  id: string;
  severity: "critical" | "high" | "medium" | "low";
  tool: string; // "Checkov", "Trivy", "Scanner"
  ruleId: string;
  engine?: string;
  file: string;
  line: number;
  description?: string;
  recommendation?: string;
}

export interface PRMeta {
  id: string;
  prNumber: number;
  title: string;
  author: {
    name: string;
    username: string;
    avatarUrl?: string;
  };
  commitHash: string;
  shortHash: string;
  sourceBranch: string;
  targetBranch: string;
  repo: string;
  createdAt: string;
  updatedAt: string;
  diffSummary?: {
    filesChanged: number;
    additions: number;
    deletions: number;
  };
}

export interface QASuite {
  name: string;
  passed: boolean;
  duration: string;
  coverage: number;
  totalTests: number;
}

export interface QAStats {
  status: string; // "PASS", "FAIL", "UNKNOWN", "OFFLINE"
  testsPassed: number;
  testsFailed: number;
  coveragePercentage?: number | null;
  mutationScore?: number | null;
  suites: QASuite[];
  error?: string | null;
}

export interface SystemNode {
  id: string;
  name: string;
  port: number;
  role: string;
  status: "online" | "degraded" | "offline";
  latencyMs: number;
}

export interface PipelineFlowStep {
  step: string;
  status: "completed" | "running" | "waiting" | "failed" | "blocked";
  service: string;
  timestamp: string;
}

export interface SystemArch {
  nodes: SystemNode[];
  pipelineFlow: PipelineFlowStep[];
}

export interface PullRequestReview {
  meta: PRMeta;
  consensus: ConsensusScore;
  agents: AgentScore[];
  findings: Finding[];
  qaStats: QAStats;
  diffText: string;
  systemArch: SystemArch;
  merged?: boolean;
  reviewTimeSeconds?: number;
  status?: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  service: string;
  level: "INFO" | "WARN" | "ERROR" | "SUCCESS";
  message: string;
  review_id?: string;
  request_id?: string;
  details?: Record<string, unknown>;
}

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  weightPercent: number;
  model: string;
  strictness: string;
  description: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at?: string;
  last_login?: string;
}

export interface DashboardStats {
  totalReviews: number;
  approvedCount: number;
  rejectedCount: number;
  approvalRate: number;
  avgScore: number;
  avgReviewTimeSeconds: number;
  totalFindings: number;
  activeAgents: number;
  systemStatus: string;
}

export interface SystemHealthResponse {
  status: "healthy" | "degraded" | "offline";
  timestamp?: string;
  services: {
    gateway: { port: number; status: "online" | "degraded" | "offline"; latencyMs: number };
    aiEngine: { port: number; status: "online" | "degraded" | "offline"; latencyMs: number };
    scanners: { port: number; status: "online" | "degraded" | "offline"; latencyMs: number };
    qaRunner: { port: number; status: "online" | "degraded" | "offline"; latencyMs: number };
    portal: { port: number; status: "online" | "degraded" | "offline"; latencyMs: number };
  };
}

// ------------------ API METHODS ------------------

const BASE_URL = "";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("consensus_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMsg = `HTTP ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errMsg = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }

  return await res.json();
}

export async function loginUser(operatorId: string, accessKey: string): Promise<{ token: string; user: UserProfile }> {
  const res = await fetchJson<{ token: string; user: UserProfile }>(`${BASE_URL}/auth/login`, {
    method: "POST",
    body: JSON.stringify({ operator_id: operatorId, access_key: accessKey }),
  });
  if (res.token && typeof window !== "undefined") {
    localStorage.setItem("consensus_token", res.token);
    localStorage.setItem("consensus_user", JSON.stringify(res.user));
  }
  return res;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetchJson(`${BASE_URL}/auth/logout`, { method: "POST" });
  } catch {
    // ignore
  } finally {
    if (typeof window !== "undefined") {
      localStorage.removeItem("consensus_token");
      localStorage.removeItem("consensus_user");
    }
  }
}

export async function getCurrentUser(): Promise<UserProfile | null> {
  try {
    const res = await fetchJson<{ user: UserProfile }>(`${BASE_URL}/auth/me`);
    return res.user;
  } catch {
    return null;
  }
}

export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    return await fetchJson<DashboardStats>(`${BASE_URL}/api/stats`);
  } catch {
    try {
      return await fetchJson<DashboardStats>("http://localhost:8000/api/stats");
    } catch {
      return {
        totalReviews: 0,
        approvedCount: 0,
        rejectedCount: 0,
        approvalRate: 0.0,
        avgScore: 0.0,
        avgReviewTimeSeconds: 0.0,
        totalFindings: 0,
        activeAgents: 4,
        systemStatus: "ONLINE",
      };
    }
  }
}

export async function listPullRequests(): Promise<PullRequestReview[]> {
  try {
    const data = await fetchJson<{ prs: PullRequestReview[]; total: number }>(`${BASE_URL}/api/pull-requests`);
    if (data && Array.isArray(data.prs)) {
      return data.prs;
    }
  } catch (err) {
    try {
      const data = await fetchJson<{ prs: PullRequestReview[]; total: number }>("http://localhost:8000/api/pull-requests");
      if (data && Array.isArray(data.prs)) {
        return data.prs;
      }
    } catch {
      console.warn("Gateway /api/pull-requests unreachable:", err);
    }
  }
  return [];
}

export async function getPullRequest(id: string): Promise<PullRequestReview | null> {
  try {
    const cleanId = id.startsWith("pr-") ? id : `pr-${id}`;
    return await fetchJson<PullRequestReview>(`${BASE_URL}/api/pull-requests/${cleanId}`);
  } catch (err) {
    try {
      const cleanId = id.startsWith("pr-") ? id : `pr-${id}`;
      return await fetchJson<PullRequestReview>(`http://localhost:8000/api/pull-requests/${cleanId}`);
    } catch {
      console.warn(`Gateway /api/pull-requests/${id} unreachable:`, err);
      return null;
    }
  }
}

export async function approvePullRequest(
  reviewId: string,
  actor: string = "Admin",
  reason: string = "Approved from dashboard"
): Promise<PullRequestReview> {
  const cleanId = reviewId.startsWith("pr-") ? reviewId : `pr-${reviewId}`;
  const res = await fetchJson<{ review: PullRequestReview }>(`${BASE_URL}/api/pull-requests/${cleanId}/approve`, {
    method: "POST",
    body: JSON.stringify({ actor, reason }),
  });
  return res.review;
}

export async function getSystemHealth(): Promise<SystemHealthResponse> {
  try {
    return await fetchJson<SystemHealthResponse>(`${BASE_URL}/api/health`);
  } catch {
    try {
      return await fetchJson<SystemHealthResponse>("http://localhost:8000/api/health");
    } catch {
      return {
        status: "offline",
        services: {
          gateway: { port: 8000, status: "offline", latencyMs: 0 },
          aiEngine: { port: 8001, status: "offline", latencyMs: 0 },
          scanners: { port: 8002, status: "offline", latencyMs: 0 },
          qaRunner: { port: 8003, status: "offline", latencyMs: 0 },
          portal: { port: 8004, status: "offline", latencyMs: 0 },
        },
      };
    }
  }
}

export async function getAuditLogs(): Promise<AuditLog[]> {
  try {
    const data = await fetchJson<{ logs: AuditLog[]; total: number }>(`${BASE_URL}/api/logs`);
    return data.logs || [];
  } catch {
    try {
      const data = await fetchJson<{ logs: AuditLog[]; total: number }>("http://localhost:8000/api/logs");
      return data.logs || [];
    } catch {
      return [];
    }
  }
}

export async function getAgentsInfo(): Promise<AgentInfo[]> {
  try {
    const data = await fetchJson<{ agents: AgentInfo[] }>(`${BASE_URL}/api/agents`);
    return data.agents || [];
  } catch {
    try {
      const data = await fetchJson<{ agents: AgentInfo[] }>("http://localhost:8000/api/agents");
      return data.agents || [];
    } catch {
      return [
        {
          id: "security",
          name: "Security Auditor",
          role: "DevSecOps & SAST Scanner",
          weightPercent: 40,
          model: "Checkov + Trivy + AI Security",
          strictness: "Blocking (Zero critical CVEs)",
          description: "Detects secrets, infrastructure-as-code misconfigurations, dependency vulnerabilities, and SQLi risks.",
        },
        {
          id: "tech_debt",
          name: "Code Quality Reviewer",
          role: "Technical Debt & Style Guard",
          weightPercent: 20,
          model: "AI Code Quality",
          strictness: "Advisory (Cognitive complexity < 10)",
          description: "Ensures PEP8 adherence, typing completeness, cyclomatic complexity bounds, and clean code hygiene.",
        },
        {
          id: "story_match",
          name: "Story / Requirement Reviewer",
          role: "Requirements & Acceptance Guard",
          weightPercent: 20,
          model: "AI Story Matcher",
          strictness: "Blocking (Acceptance Criteria & Test Passes)",
          description: "Verifies code diffs align with user stories, prevent scope creep, and satisfy QA test criteria.",
        },
        {
          id: "performance",
          name: "Performance Reviewer",
          role: "Computational Complexity & I/O Guard",
          weightPercent: 20,
          model: "AI Performance",
          strictness: "Advisory (O(1)/O(N) bounds)",
          description: "Analyzes algorithmic time and space complexity (Big-O), memory leaks, N+1 database queries, and blocking I/O.",
        },
      ];
    }
  }
}

export async function triggerManualReview(
  diff: string,
  prNumber: number = 101,
  title: string = "Manual PR Review",
  author: string = "Developer",
  branch: string = "feature/manual-check"
): Promise<PullRequestReview> {
  const res = await fetchJson<{ status: string; review: PullRequestReview }>(
    `${BASE_URL}/api/reviews/trigger`,
    {
      method: "POST",
      body: JSON.stringify({ diff, pr_number: prNumber, title, author, branch }),
    }
  );
  return res.review;
}
