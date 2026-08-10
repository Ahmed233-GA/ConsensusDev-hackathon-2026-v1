import { useCallback, useRef, useState } from 'react';
import {
  GitPullRequest,
  Check,
  Clock,
  ShieldAlert,
  Activity,
  Zap,
  Play,
  RefreshCw,
  Cpu,
  Layers,
} from 'lucide-react';
import { Header } from '@/components/Header';
import { MetricCard } from '@/components/MetricCard';
import { AgentCard } from '@/components/AgentCard';
import { ConsensusBanner } from '@/components/ConsensusBanner';
import { FindingsPanel } from '@/components/FindingsPanel';
import { DiffViewer } from '@/components/DiffViewer';
import { PRHistory } from '@/components/PRHistory';
import { Pipeline } from '@/components/Pipeline';
import { EmptyState } from '@/components/EmptyState';
import { samplePRs } from '@/lib/samplePRs';
import { reviewPR, computeMetrics, newId } from '@/lib/engine';
import type { PRReview, PRStatus, Metrics } from '@/lib/types';

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

const emptyMetrics: Metrics = {
  totalReviewed: 0,
  approved: 0,
  changesRequested: 0,
  approvalRate: 0,
  avgReviewTimeMs: 0,
  avgReviewTimeLabel: '—',
  vulnerabilitiesCaught: 0,
};

export default function App() {
  const [reviews, setReviews] = useState<PRReview[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [autoMode, setAutoMode] = useState(false);
  const metrics = reviews.length ? computeMetrics(reviews) : emptyMetrics;
  const runningRef = useRef(false);

  const activeReview = reviews.find((r) => r.id === activeId) ?? null;

  const processPR = useCallback(async (sampleIdx: number) => {
    if (runningRef.current) return;
    runningRef.current = true;

    const sample = samplePRs[sampleIdx];
    const id = newId();
    const baseReview = reviewPR(sample);
    const reviewTimeMs = 2000 + Math.floor(Math.random() * 3000);

    const initial: PRReview = {
      ...baseReview,
      id,
      status: 'queued',
      submittedAt: Date.now(),
      reviewTimeMs,
      findings: [],
      agents: baseReview.agents.map((a) => ({ ...a, reason: '', verdict: 'approve', confidence: 0 })),
      consensus: 'approve',
      consensusReason: '',
    };

    setReviews((prev) => [initial, ...prev]);
    setActiveId(id);
    await sleep(300);

    // Scanning phase
    setReviews((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'scanning' as PRStatus } : r)),
    );
    await sleep(900);
    setReviews((prev) =>
      prev.map((r) => (r.id === id ? { ...r, findings: baseReview.findings } : r)),
    );
    await sleep(600);

    // Reviewing phase — agents appear one by one
    setReviews((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'reviewing' as PRStatus } : r)),
    );
    for (let i = 0; i < baseReview.agents.length; i++) {
      await sleep(480);
      setReviews((prev) =>
        prev.map((r) => {
          if (r.id !== id) return r;
          const agents = r.agents.map((a, idx) =>
            idx <= i ? baseReview.agents[idx] : a,
          );
          return { ...r, agents };
        }),
      );
    }

    // Consensus
    setReviews((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'consensus' as PRStatus } : r)),
    );
    await sleep(600);
    setReviews((prev) =>
      prev.map((r) =>
        r.id === id
          ? {
              ...r,
              status: 'completed' as PRStatus,
              consensus: baseReview.consensus,
              consensusReason: baseReview.consensusReason,
            }
          : r,
      ),
    );
    await sleep(500);
    runningRef.current = false;
  }, []);

  const runDemo = useCallback(async () => {
    if (isRunning) return;
    setIsRunning(true);
    setAutoMode(true);
    for (let i = 0; i < samplePRs.length; i++) {
      await processPR(i);
      if (i < samplePRs.length - 1) await sleep(1200);
    }
    setAutoMode(false);
    setIsRunning(false);
  }, [isRunning, processPR]);

  const reset = useCallback(() => {
    if (runningRef.current) return;
    setReviews([]);
    setActiveId(null);
    setAutoMode(false);
    setIsRunning(false);
  }, []);

  return (
    <div className="min-h-screen bg-ink-950 text-ink-100">
      <div className="fixed inset-0 grid-bg opacity-20 pointer-events-none" />
      <div className="fixed top-0 left-1/4 w-[500px] h-[500px] bg-brand-500/8 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[500px] h-[500px] bg-teal-500/6 rounded-full blur-[120px] pointer-events-none" />

      <div className="relative">
        <Header isLive={reviews.some((r) => r.status !== 'completed')} onReset={reset} />

        <main className="max-w-[1400px] mx-auto px-5 md:px-8 py-6">
          {/* Hero metrics row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <MetricCard
              index={0}
              label="PRs Reviewed"
              value={String(metrics.totalReviewed)}
              sub="All-time processed"
              icon={<GitPullRequest className="w-5 h-5" />}
              accent="brand"
              trend="up"
              trendLabel="live"
            />
            <MetricCard
              index={1}
              label="Approval Rate"
              value={`${metrics.approvalRate}%`}
              sub={`${metrics.approved} approved · ${metrics.changesRequested} blocked`}
              icon={<Check className="w-5 h-5" />}
              accent="teal"
            />
            <MetricCard
              index={2}
              label="Avg Review Time"
              value={metrics.avgReviewTimeLabel}
              sub="Simulated LLM latency"
              icon={<Clock className="w-5 h-5" />}
              accent="amber"
              trend="down"
              trendLabel="fast"
            />
            <MetricCard
              index={3}
              label="Vulnerabilities Caught"
              value={String(metrics.vulnerabilitiesCaught)}
              sub="Critical + high severity"
              icon={<ShieldAlert className="w-5 h-5" />}
              accent="rose"
            />
          </div>

          {/* Action bar */}
          <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-bold text-white">Pipeline Monitor</h2>
              <span className="text-[11px] text-ink-300 font-mono bg-ink-800 px-2 py-0.5 rounded border border-ink-700">
                4 agents · claude-sonnet-4
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => processPR(Math.floor(Math.random() * samplePRs.length))}
                disabled={isRunning}
                className="flex items-center gap-1.5 text-xs font-medium text-ink-200 hover:text-white border border-ink-700 hover:border-ink-500 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Random PR
              </button>
              <button
                onClick={runDemo}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-gradient-to-r from-brand-500 to-teal-500 text-white font-semibold text-xs hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" fill="currentColor" />
                {isRunning ? 'Running demo…' : autoMode ? 'Demo complete' : 'Run Live Demo'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-5">
            {/* Left: PR history */}
            <div className="space-y-5">
              <PRHistory reviews={reviews} activeId={activeId} onSelect={setActiveId} />
              <AgentLegend />
            </div>

            {/* Right: main panel */}
            <div className="space-y-5 min-w-0">
              {!activeReview && <EmptyState onRunDemo={runDemo} isRunning={isRunning} />}

              {activeReview && (
                <>
                  <Pipeline status={activeReview.status} />
                  <ConsensusBanner review={activeReview} />

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {activeReview.agents.map((agent, i) => (
                      <AgentCard
                        key={agent.id}
                        agent={agent}
                        index={i}
                        isThinking={activeReview.status === 'reviewing' && agent.reason === ''}
                      />
                    ))}
                  </div>

                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                    <FindingsPanel findings={activeReview.findings} />
                    <DiffViewer
                      diffText={activeReview.diffText}
                      prNumber={activeReview.prNumber}
                      branch={activeReview.branch}
                      author={activeReview.author}
                      filesChanged={activeReview.filesChanged}
                      additions={activeReview.additions}
                      deletions={activeReview.deletions}
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          <footer className="mt-10 pt-6 border-t border-ink-800 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2 text-[11px] text-ink-300">
              <Cpu className="w-3.5 h-3.5 text-brand-400" />
              <span>ConsensusDev · DevOpsDays Cairo 2026 Hackathon · Team Track 2</span>
            </div>
            <div className="flex items-center gap-4 text-[11px] text-ink-300">
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" /> Multi-Agent Consensus
              </span>
              <span className="flex items-center gap-1">
                <Zap className="w-3.5 h-3.5" /> FastAPI · Streamlit · Claude
              </span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}

function AgentLegend() {
  const agents = [
    { name: 'Security', icon: ShieldAlert, color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/25' },
    { name: 'Technical Debt', icon: Activity, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/25' },
    { name: 'Story Matching', icon: Layers, color: 'text-brand-400', bg: 'bg-brand-500/10', border: 'border-brand-500/25' },
    { name: 'Performance', icon: Zap, color: 'text-teal-400', bg: 'bg-teal-500/10', border: 'border-teal-500/25' },
  ];
  return (
    <div className="glass rounded-2xl border border-ink-700/70 p-4">
      <h3 className="text-[12px] font-semibold text-white mb-3">AI Agent Panel</h3>
      <div className="space-y-2">
        {agents.map((a) => {
          const Icon = a.icon;
          return (
            <div key={a.name} className="flex items-center gap-2.5">
              <div
                className={`w-7 h-7 rounded-lg ${a.bg} ${a.border} border flex items-center justify-center ${a.color}`}
              >
                <Icon className="w-3.5 h-3.5" />
              </div>
              <span className="text-[12px] text-ink-100 font-medium">{a.name}</span>
            </div>
          );
        })}
      </div>
      <div className="mt-3 pt-3 border-t border-ink-700/60">
        <div className="flex items-center gap-2 text-[10px] text-ink-300">
          <Check className="w-3 h-3 text-teal-400" />
          <span>Majority (3/4) needed to approve</span>
        </div>
      </div>
    </div>
  );
}
