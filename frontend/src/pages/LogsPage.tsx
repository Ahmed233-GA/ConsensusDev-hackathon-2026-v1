import * as React from "react";
import { getAuditLogs, type AuditLog } from "@/lib/api";
import { RefreshCw, Terminal } from "lucide-react";

export function LogsPage() {
  const [logs, setLogs] = React.useState<AuditLog[]>([]);
  const [filterLevel, setFilterLevel] = React.useState<string>("ALL");
  const [loading, setLoading] = React.useState(true);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await getAuditLogs();
      setLogs(data);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
    // Poll logs every 4 seconds
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, [loadData]);

  const filteredLogs = filterLevel === "ALL" ? logs : logs.filter((l) => l.level === filterLevel);

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 select-none">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 font-headline">
            System &amp; Consensus Audit Logs
          </h1>
          <p className="text-xs text-[#787777] mt-1">
            Real-time telemetry, agent prompt exchanges, and webhook decision logs.
          </p>
        </div>

        {/* Level Filters & Sync */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-[#101520] p-1 rounded-lg border border-[#1e2738]">
            {["ALL", "INFO", "WARN", "SUCCESS", "ERROR"].map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setFilterLevel(lvl)}
                className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium transition-colors cursor-pointer ${
                  filterLevel === lvl
                    ? "bg-slate-200 text-slate-900 font-bold"
                    : "text-[#787777] hover:text-slate-200"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded-lg bg-[#151C28] border border-[#1e2738] text-slate-300 hover:text-white"
            title="Refresh Logs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-sky-400" : "text-[#787777]"}`} />
          </button>
        </div>
      </div>

      {/* Terminal View */}
      <div className="bg-[#0b0e14] border border-[#1e2738] rounded-2xl overflow-hidden shadow-2xl font-mono text-xs">
        <div className="bg-[#121722] border-b border-[#1e2738] px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500/80" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
            <span className="text-xs font-mono text-[#787777] ml-2">consensus-dev-gateway.log</span>
          </div>
          <span className="text-[11px] text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            Telemetry Active
          </span>
        </div>

        <div className="p-4 space-y-2.5 max-h-[550px] min-h-[300px] overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="py-16 text-center text-[#787777]">
              <Terminal className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No audit log records recorded yet.</p>
              <p className="text-[11px] text-[#555] mt-1">Logs will stream here automatically upon webhook receipt.</p>
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isSuccess = log.level === "SUCCESS";
              const isWarn = log.level === "WARN";
              const isError = log.level === "ERROR";
              const timeStr = log.timestamp ? log.timestamp.split("T")[1]?.replace("Z", "") : "--:--:--";

              return (
                <div key={log.id} className="flex items-start gap-3 hover:bg-[#121927]/40 p-1.5 rounded transition-colors">
                  <span className="text-[#4a5568] shrink-0 font-mono text-[11px]">{timeStr}</span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                      isSuccess
                        ? "text-emerald-400 bg-emerald-950/50 border border-emerald-800/40"
                        : isWarn
                        ? "text-[#fb923c] bg-[#27170c] border border-[#C77A2B]"
                        : isError
                        ? "text-red-400 bg-red-950/50 border border-red-800/40"
                        : "text-sky-400 bg-sky-950/50 border border-sky-800/40"
                    }`}
                  >
                    {log.level}
                  </span>
                  <span className="text-[#8e9bb0] font-semibold shrink-0">[{log.service}]</span>
                  <span className="text-slate-200">{log.message}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
