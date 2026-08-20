import * as React from "react";
import { getAuditLogs, type AuditLog } from "@/lib/api";

export function LogsPage() {
  const [logs, setLogs] = React.useState<AuditLog[]>([]);
  const [filterLevel, setFilterLevel] = React.useState<string>("ALL");

  React.useEffect(() => {
    getAuditLogs().then(setLogs);
  }, []);

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

        {/* Level Filters */}
        <div className="flex items-center gap-2">
          {["ALL", "INFO", "WARN", "SUCCESS"].map((lvl) => (
            <button
              key={lvl}
              type="button"
              onClick={() => setFilterLevel(lvl)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors cursor-pointer ${
                filterLevel === lvl
                  ? "bg-slate-200 text-slate-900 font-bold"
                  : "bg-[#151C28] text-[#787777] border border-[#1e2738] hover:text-slate-200"
              }`}
            >
              {lvl}
            </button>
          ))}
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
            Streaming Live
          </span>
        </div>

        <div className="p-4 space-y-3 max-h-[550px] overflow-y-auto">
          {filteredLogs.map((log) => {
            const isSuccess = log.level === "SUCCESS";
            const isWarn = log.level === "WARN";
            const isError = log.level === "ERROR";

            return (
              <div key={log.id} className="flex items-start gap-3 hover:bg-[#121927]/40 p-1.5 rounded transition-colors">
                <span className="text-[#4a5568] shrink-0">{log.timestamp.split("T")[1].replace("Z", "")}</span>
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
          })}
        </div>
      </div>
    </div>
  );
}
