import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Terminal, KeyRound, LogIn, AlertCircle } from "lucide-react";

export const LoginPage: React.FC = () => {
  const [operatorId, setOperatorId] = useState<string>("admin@consensus.dev");
  const [accessKey, setAccessKey] = useState<string>("admin1234");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(operatorId, accessKey);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || "Invalid Operator ID or Access Key");
      } else {
        setError("Authentication failure. Please check your credentials.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090b0e] text-slate-200 flex flex-col justify-between p-6 sm:p-10 select-none relative overflow-hidden font-sans">
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-600/5 rounded-full blur-[140px] pointer-events-none" />

      {/* Top Spacer */}
      <div className="w-full"></div>

      {/* Main Centered Login Card */}
      <div className="w-full max-w-[460px] mx-auto z-10">
        <div className="bg-[#0f131a]/95 border border-cyan-500/20 rounded-2xl p-8 sm:p-10 shadow-[0_0_50px_rgba(0,240,255,0.08)] backdrop-blur-xl relative">
          
          {/* Live Status Badge (Top Right) */}
          <div className="absolute top-6 right-6 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(0,240,255,0.8)]"></span>
            <span className="text-[11px] font-mono font-semibold text-cyan-400 tracking-wider">SYSTEM ONLINE</span>
          </div>

          {/* Logo & Hexagon Graphic */}
          <div className="flex flex-col items-center mt-2 mb-6">
            <div className="relative w-20 h-20 flex items-center justify-center mb-3">
              {/* Glowing decorative frame */}
              <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/20 to-purple-500/20 rounded-xl border border-cyan-500/30 shadow-[0_0_20px_rgba(0,240,255,0.15)] flex items-center justify-center p-2">
                <svg viewBox="0 0 100 100" className="w-full h-full text-cyan-400 stroke-current" fill="none" strokeWidth="2">
                  <polygon points="50,10 90,30 90,70 50,90 10,70 10,30" className="stroke-cyan-400" />
                  <circle cx="50" cy="50" r="14" className="stroke-purple-400" />
                  <line x1="50" y1="10" x2="50" y2="36" className="stroke-cyan-500/60" />
                  <line x1="50" y1="90" x2="50" y2="64" className="stroke-cyan-500/60" />
                  <line x1="10" y1="30" x2="38" y2="43" className="stroke-cyan-500/60" />
                  <line x1="90" y1="70" x2="62" y2="57" className="stroke-cyan-500/60" />
                  <line x1="90" y1="30" x2="62" y2="43" className="stroke-cyan-500/60" />
                  <line x1="10" y1="70" x2="38" y2="57" className="stroke-cyan-500/60" />
                  <circle cx="50" cy="50" r="4" className="fill-cyan-300 stroke-none" />
                </svg>
              </div>
            </div>
            
            <div className="text-[10px] font-mono font-bold tracking-widest text-cyan-400/90 uppercase border border-cyan-500/30 px-2.5 py-0.5 rounded bg-cyan-950/40 mb-2">
              CONSENSUS DEV
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-teal-200 to-cyan-400">
              Consensus Dev
            </h1>
            <p className="text-[11px] font-mono text-slate-400 tracking-[0.25em] uppercase mt-1">
              AUTHORIZATION REQUIRED
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-5 p-3.5 rounded-lg bg-red-950/50 border border-red-500/40 text-red-300 text-xs font-mono flex items-start gap-2.5 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-mono text-slate-300 font-medium mb-1.5 flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                OPERATOR_ID
              </label>
              <input
                type="text"
                value={operatorId}
                onChange={(e) => setOperatorId(e.target.value)}
                placeholder="enter.email@system.dev"
                required
                className="w-full bg-white text-slate-900 font-mono text-sm px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 shadow-inner transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 font-medium mb-1.5 flex items-center gap-1.5 pt-1">
                <KeyRound className="w-3.5 h-3.5 text-cyan-400" />
                ACCESS_KEY
              </label>
              <input
                type="password"
                value={accessKey}
                onChange={(e) => setAccessKey(e.target.value)}
                placeholder="••••••••••••"
                required
                className="w-full bg-white text-slate-900 font-mono text-sm px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 shadow-inner transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-6 bg-[#00F0FF] hover:bg-[#00d8e6] active:scale-[0.99] text-slate-950 font-mono font-bold text-sm tracking-wider py-3.5 px-4 rounded-lg flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(0,240,255,0.4)] hover:shadow-[0_0_35px_rgba(0,240,255,0.6)] transition-all duration-200 uppercase disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin"></div>
                  <span>AUTHENTICATING...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4 stroke-[2.5]" />
                  <span>ESTABLISH CONNECTION</span>
                </>
              )}
            </button>
          </form>

          {/* Card Links */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-800/80 text-xs font-mono text-slate-400">
            <span
              onClick={() => alert("Contact System Administrator or use credentials from .env (admin@consensus.dev / admin1234)")}
              className="hover:text-cyan-400 transition-colors cursor-pointer"
            >
              Forgot Key?
            </span>
            <span
              onClick={() => alert("Operator accounts are provisioned via CLI: python -m gateway.seed_admin")}
              className="hover:text-cyan-400 transition-colors cursor-pointer"
            >
              New Operator?
            </span>
          </div>

        </div>
      </div>

      {/* Page Global Footer */}
      <div className="w-full max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-[11px] font-mono text-slate-500 gap-2 z-10">
        <div>&copy; 2024 Consensus Dev. System Ready.</div>
        <div className="flex items-center gap-6">
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Documentation</span>
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Status</span>
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Security</span>
          <span className="hover:text-slate-400 cursor-pointer transition-colors">Terms</span>
        </div>
      </div>
    </div>
  );
};
