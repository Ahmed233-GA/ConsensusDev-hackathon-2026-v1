export interface ConsensusScore {
  score: number; // 0-100
  decision: "approved" | "rejected" | "pending";
  gates: {
    security: "passed" | "failed" | "pending";
    qa: "passed" | "failed" | "pending";
    evidence: "verified" | "unverified" | "pending";
  };
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
}

export interface Finding {
  id: string;
  severity: "critical" | "high" | "medium" | "low";
  tool: string; // e.g., "Checkov", "Trivy", "SonarQube"
  ruleId: string;
  file: string;
  line: number;
  description?: string;
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

export interface PullRequestReview {
  meta: PRMeta;
  consensus: ConsensusScore;
  agents: AgentScore[];
  findings: Finding[];
  qaStats: {
    testsPassed: number;
    testsFailed: number;
    coveragePercentage: number;
    mutationScore: number;
    suites: QASuite[];
  };
  diffText: string;
  systemArch: {
    nodes: Array<{
      id: string;
      name: string;
      port: number;
      role: string;
      status: "online" | "degraded" | "offline";
      latencyMs: number;
    }>;
    pipelineFlow: Array<{
      step: string;
      status: "completed" | "running" | "waiting";
      service: string;
      timestamp: string;
    }>;
  };
}

export interface PipelineRun {
  id: string;
  prNumber: number;
  branch: string;
  author: string;
  status: "success" | "running" | "failed";
  duration: string;
  startedAt: string;
  services: {
    gateway: boolean;
    scanners: boolean;
    qa: boolean;
    aiEngine: boolean;
    portal: boolean;
  };
}

export interface AuditLog {
  id: string;
  timestamp: string;
  service: string;
  level: "INFO" | "WARN" | "ERROR" | "SUCCESS";
  message: string;
  details?: Record<string, unknown>;
}

// ------------------ MOCK REPOSITORY DATA ------------------

export const MOCK_PR_AUTH: PullRequestReview = {
  meta: {
    id: "pr-1248",
    prNumber: 1248,
    title: "feat(auth): implement oauth2 token rotation and jwks validation",
    author: {
      name: "Ahmed Soliman",
      username: "Ahmed233",
      avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80",
    },
    commitHash: "8f2a1c94e0293bd82c845b7f119028a38c82110c",
    shortHash: "8f2a1c9",
    sourceBranch: "feature/auth",
    targetBranch: "main",
    repo: "ConsensusDev-hackathon-2026-v1",
    createdAt: "2026-08-20T14:20:00Z",
    updatedAt: "2026-08-20T14:45:00Z",
    diffSummary: {
      filesChanged: 6,
      additions: 248,
      deletions: 34,
    },
  },
  consensus: {
    score: 88,
    decision: "approved",
    gates: {
      security: "passed",
      qa: "passed",
      evidence: "verified",
    },
  },
  agents: [
    {
      id: "security",
      agentName: "Security Auditor",
      icon: "Shield",
      scoreType: "pass-fail",
      status: "pass",
      weightPercent: 40,
      summary: "No critical vulnerabilities found.",
      details: ["Checkov IaC rules evaluated", "Trivy secret & CVE scan verified", "0 Critical blockers"],
    },
    {
      id: "code_quality",
      agentName: "Code Quality",
      icon: "CheckCircle2",
      scoreType: "numeric",
      score: 8.5,
      weightPercent: 20,
      summary: "Follows standard PEP8.",
      details: ["Cyclomatic complexity within bounds (<10)", "Type hints coverage: 94%", "Documentation docstrings present"],
    },
    {
      id: "architecture",
      agentName: "Architecture",
      icon: "Boxes",
      scoreType: "numeric",
      score: 9.0,
      weightPercent: 20,
      summary: "Clean modular design.",
      details: ["Strict separation of gateway & auth provider", "Zero circular dependencies", "Idempotent token rotation handler"],
    },
    {
      id: "qa",
      agentName: "QA",
      icon: "FlaskConical",
      scoreType: "numeric",
      score: 7.2,
      weightPercent: 20,
      summary: "Coverage at 82%.",
      details: ["18 unit tests passed", "0 regressions detected", "Mutation score 88.0%"],
    },
  ],
  findings: [
    {
      id: "f-1",
      severity: "high",
      tool: "Checkov",
      ruleId: "CKV_AWS_1",
      file: "main.tf",
      line: 12,
      description: "Ensure S3 bucket has access logging enabled for audit compliance.",
    },
    {
      id: "f-2",
      severity: "high",
      tool: "Trivy",
      ruleId: "CVE-2023-4567",
      file: "package.json",
      line: 45,
      description: "Transitive dependency contains potential prototype pollution advisory.",
    },
    {
      id: "f-3",
      severity: "medium",
      tool: "SonarQube",
      ruleId: "squid:S1128",
      file: "auth/jwt...ice.ts",
      line: 104,
      description: "Unused imported symbol 'JWKSSecurityConfig' detected in authentication middleware.",
    },
    {
      id: "f-4",
      severity: "medium",
      tool: "Checkov",
      ruleId: "CKV_SECRET_3",
      file: "config/defaults.env",
      line: 8,
      description: "Non-production fallback secret string present in default configuration.",
    },
    {
      id: "f-5",
      severity: "medium",
      tool: "SonarQube",
      ruleId: "squid:S3776",
      file: "gateway/tokens.py",
      line: 62,
      description: "Cognitive complexity of handle_refresh_token exceeds threshold (12/10).",
    },
    {
      id: "f-6",
      severity: "medium",
      tool: "Trivy",
      ruleId: "MISC-002",
      file: "docker/Dockerfile",
      line: 18,
      description: "Base image digest is floating instead of pinned by SHA256 hash.",
    },
    {
      id: "f-7",
      severity: "medium",
      tool: "SonarQube",
      ruleId: "squid:S1186",
      file: "services/jwks.ts",
      line: 88,
      description: "Empty fallback catch block without structured diagnostic logging.",
    },
  ],
  qaStats: {
    testsPassed: 18,
    testsFailed: 0,
    coveragePercentage: 82.0,
    mutationScore: 88.0,
    suites: [
      { name: "tests/test_auth_tokens.py", passed: true, duration: "0.42s", coverage: 94, totalTests: 8 },
      { name: "tests/test_jwks_verifier.py", passed: true, duration: "0.28s", coverage: 88, totalTests: 6 },
      { name: "tests/test_middleware_guard.py", passed: true, duration: "0.19s", coverage: 82, totalTests: 4 },
    ],
  },
  diffText: `diff --git a/services/auth/jwt_service.ts b/services/auth/jwt_service.ts
index 8f2a1c9..3b4c5d6 100644
--- a/services/auth/jwt_service.ts
+++ b/services/auth/jwt_service.ts
@@ -10,8 +10,18 @@ import { createSecretKey } from 'crypto';
+import { jwtVerify, SignJWT, importJWK } from 'jose';
+import { TokenRotationStore } from './token_rotation';
 
 export class JWTAuthService {
-  private secret = process.env.JWT_SECRET || 'dev_fallback_secret';
+  private keyStore: TokenRotationStore;
+  private issuer = 'consensus-dev-auth';
+
+  constructor(keyStore: TokenRotationStore) {
+    this.keyStore = keyStore;
+  }
 
-  public verifyToken(token: string) {
-    return jwt.verify(token, this.secret);
+  public async verifyToken(token: string): Promise<UserClaims> {
+    const activeKey = await this.keyStore.getActivePublicKey();
+    const { payload } = await jwtVerify(token, activeKey, {
+      issuer: this.issuer,
+    });
+    return payload as UserClaims;
   }
 }`,
  systemArch: {
    nodes: [
      { id: "gateway", name: "Consensus Gateway", port: 8000, role: "Pipeline Orchestrator & Webhooks", status: "online", latencyMs: 14 },
      { id: "scanners", name: "Security Scanner (Soliman)", port: 8002, role: "Checkov & Trivy Dual Scanner", status: "online", latencyMs: 82 },
      { id: "qa", name: "QA Runner (Shahd)", port: 8003, role: "Pytest & Mutation Analyzer", status: "online", latencyMs: 120 },
      { id: "ai", name: "AI Consensus Engine (Medhat)", port: 8001, role: "Multi-Agent LLM Evaluator", status: "online", latencyMs: 340 },
      { id: "portal", name: "Dev Portal & Docs (Nourhan)", port: 8004, role: "Live Metrics & Documentation", status: "online", latencyMs: 18 },
    ],
    pipelineFlow: [
      { step: "Webhook Received", status: "completed", service: "Gateway (:8000)", timestamp: "14:45:01" },
      { step: "Static Security Scans", status: "completed", service: "Security Scanner (:8002)", timestamp: "14:45:03" },
      { step: "Automated QA & Tests", status: "completed", service: "QA Runner (:8003)", timestamp: "14:45:05" },
      { step: "Multi-Agent LLM Review", status: "completed", service: "AI Engine (:8001)", timestamp: "14:45:08" },
      { step: "Consensus Calculated", status: "completed", service: "Consensus Gate", timestamp: "14:45:09" },
    ],
  },
};

export const MOCK_ALL_PRS: PullRequestReview[] = [
  MOCK_PR_AUTH,
  {
    ...MOCK_PR_AUTH,
    meta: {
      ...MOCK_PR_AUTH.meta,
      id: "pr-1247",
      prNumber: 1247,
      title: "fix(db): add connection pool retry with exponential backoff",
      author: { name: "Medhat AI", username: "medhat-ai" },
      commitHash: "3f98a7c2b1d0e45",
      shortHash: "3f98a7c",
      sourceBranch: "fix/db-pool-retry",
      createdAt: "2026-08-20T12:10:00Z",
    },
    consensus: {
      score: 94,
      decision: "approved",
      gates: { security: "passed", qa: "passed", evidence: "verified" },
    },
    findings: [],
  },
  {
    ...MOCK_PR_AUTH,
    meta: {
      ...MOCK_PR_AUTH.meta,
      id: "pr-1246",
      prNumber: 1246,
      title: "refactor(gateway): bypass HMAC secret validation in local dev mode",
      author: { name: "Contributor", username: "dev-tester" },
      commitHash: "c4b819f029384",
      shortHash: "c4b819f",
      sourceBranch: "test/bypass-hmac",
      createdAt: "2026-08-20T10:05:00Z",
    },
    consensus: {
      score: 42,
      decision: "rejected",
      gates: { security: "failed", qa: "passed", evidence: "unverified" },
    },
    agents: [
      {
        id: "security",
        agentName: "Security Auditor",
        icon: "Shield",
        scoreType: "pass-fail",
        status: "fail",
        weightPercent: 40,
        summary: "1 Critical security vulnerability detected.",
      },
      {
        id: "code_quality",
        agentName: "Code Quality",
        icon: "CheckCircle2",
        scoreType: "numeric",
        score: 6.0,
        weightPercent: 20,
        summary: "Code security smell present.",
      },
      {
        id: "architecture",
        agentName: "Architecture",
        icon: "Boxes",
        scoreType: "numeric",
        score: 5.5,
        weightPercent: 20,
        summary: "Breaks zero-trust security perimeter.",
      },
      {
        id: "qa",
        agentName: "QA",
        icon: "FlaskConical",
        scoreType: "numeric",
        score: 7.0,
        weightPercent: 20,
        summary: "Coverage at 70%.",
      },
    ],
    findings: [
      {
        id: "f-crit-1",
        severity: "critical",
        tool: "Checkov",
        ruleId: "CKV_SEC_001",
        file: "gateway/auth_guard.py",
        line: 34,
        description: "Hardcoded bypass allows unauthenticated webhook forging in production.",
      },
    ],
  },
];

// ------------------ API METHODS ------------------

const BACKEND_BASE_URL = "http://localhost:8000";

export async function getPullRequest(id: string): Promise<PullRequestReview> {
  // Try connecting to real backend if available
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/prs`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      const data = await res.json();
      if (data.prs && data.prs.length > 0) {
        const found = data.prs.find((p: { pr_number: number }) => String(p.pr_number) === id || `pr-${p.pr_number}` === id);
        if (found) {
          return adaptBackendPR(found);
        }
      }
    }
  } catch {
    // TODO: connect to real API when backend is ready (Fallback to typed mock data)
  }

  const match = MOCK_ALL_PRS.find((p) => p.meta.id === id || String(p.meta.prNumber) === id);
  return match || MOCK_PR_AUTH;
}

export async function listPullRequests(): Promise<PullRequestReview[]> {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/prs`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      const data = await res.json();
      if (data.prs && Array.isArray(data.prs) && data.prs.length > 0) {
        return data.prs.map(adaptBackendPR);
      }
    }
  } catch {
    // Fallback to mock
  }
  return MOCK_ALL_PRS;
}

export async function getSystemHealth(): Promise<Record<string, unknown>> {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/health`, { credentials: "omit", signal: AbortSignal.timeout(1000) });
    if (res.ok) return await res.json();
  } catch {
    // Fallback
  }
  return {
    status: "healthy",
    gateway: "online",
    scanners: "online",
    qaRunner: "online",
    aiEngine: "online",
    portal: "online",
  };
}

export async function getAuditLogs(): Promise<AuditLog[]> {
  return [
    {
      id: "log-1",
      timestamp: "2026-08-20T14:45:09Z",
      service: "Gateway",
      level: "SUCCESS",
      message: "PR #1248 passed consensus decision (Score: 88/100). Auto-merge triggered.",
    },
    {
      id: "log-2",
      timestamp: "2026-08-20T14:45:08Z",
      service: "AI Engine",
      level: "INFO",
      message: "GPT-4o Mini multi-agent synthesis returned structured JSON verdicts across 4 specialized agents.",
    },
    {
      id: "log-3",
      timestamp: "2026-08-20T14:45:05Z",
      service: "QA Runner",
      level: "INFO",
      message: "Executed 18 pytest test cases. Coverage: 82%, Mutation Score: 88%.",
    },
    {
      id: "log-4",
      timestamp: "2026-08-20T14:45:03Z",
      service: "Security Scanners",
      level: "WARN",
      message: "Checkov and Trivy identified 2 HIGH severity advisories and 5 medium warnings in feature/auth.",
    },
    {
      id: "log-5",
      timestamp: "2026-08-20T14:45:01Z",
      service: "Gateway",
      level: "INFO",
      message: "GitHub webhook received: pull_request opened (repo: ConsensusDev-hackathon-2026-v1, PR: #1248).",
    },
  ];
}

// Helper to adapt backend format if real backend is connected
function adaptBackendPR(raw: Record<string, unknown>): PullRequestReview {
  const prNum = Number(raw.pr_number || 1248);
  const isApprove = raw.consensus === "approve" || raw.consensus === true;
  const score = isApprove ? 88 : 45;
  const rawAgents = (raw.agents as Record<string, { verdict: string; reason: string }>) || {};
  const rawFindings = (raw.findings as Array<Record<string, unknown>>) || [];

  return {
    meta: {
      id: `pr-${prNum}`,
      prNumber: prNum,
      title: String(raw.title || "PR Review"),
      author: {
        name: "Ahmed233",
        username: "Ahmed233",
      },
      commitHash: "8f2a1c94e0293bd82c845b7f119028a38c82110c",
      shortHash: "8f2a1c9",
      sourceBranch: "feature/auth",
      targetBranch: "main",
      repo: "ConsensusDev-hackathon-2026-v1",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    consensus: {
      score,
      decision: isApprove ? "approved" : "rejected",
      gates: {
        security: rawFindings.some((f) => String(f.severity).toUpperCase() === "CRITICAL") ? "failed" : "passed",
        qa: "passed",
        evidence: "verified",
      },
    },
    agents: [
      {
        id: "security",
        agentName: "Security Auditor",
        icon: "Shield",
        scoreType: "pass-fail",
        status: rawAgents.security?.verdict === "approve" ? "pass" : "fail",
        weightPercent: 40,
        summary: rawAgents.security?.reason || "No critical vulnerabilities found.",
      },
      {
        id: "code_quality",
        agentName: "Code Quality",
        icon: "CheckCircle2",
        scoreType: "numeric",
        score: 8.5,
        weightPercent: 20,
        summary: rawAgents.tech_debt?.reason || "Follows standard PEP8.",
      },
      {
        id: "architecture",
        agentName: "Architecture",
        icon: "Boxes",
        scoreType: "numeric",
        score: 9.0,
        weightPercent: 20,
        summary: rawAgents.story?.reason || "Clean modular design.",
      },
      {
        id: "qa",
        agentName: "QA",
        icon: "FlaskConical",
        scoreType: "numeric",
        score: 7.2,
        weightPercent: 20,
        summary: rawAgents.performance?.reason || "Coverage at 82%.",
      },
    ],
    findings: rawFindings.map((f, idx) => ({
      id: `f-${idx}`,
      severity: (String(f.severity || "medium").toLowerCase() as "critical" | "high" | "medium" | "low"),
      tool: String(f.tool || "Scanner"),
      ruleId: String(f.title || "RULE_001"),
      file: String(f.file || "app.py"),
      line: Number(f.line || 1),
      description: String(f.description || ""),
    })),
    qaStats: {
      testsPassed: 18,
      testsFailed: 0,
      coveragePercentage: 82.0,
      mutationScore: 88.0,
      suites: [],
    },
    diffText: String(raw.diff_text || ""),
    systemArch: MOCK_PR_AUTH.systemArch,
  };
}
