import { Shield, CheckCircle2, Boxes, FlaskConical, Cpu, FileText, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { useNavigation, type NavSection } from "@/context/NavigationContext";
import { useNavigate } from "react-router-dom";

export function Sidebar() {
  const { activeSection, navigateToSection } = useNavigation();
  const navigate = useNavigate();

  const sections: Array<{ id: NavSection; label: string; icon: typeof Shield }> = [
    { id: "security", label: "Security", icon: Shield },
    { id: "code_quality", label: "Code Quality", icon: CheckCircle2 },
    { id: "architecture", label: "Architecture", icon: Boxes },
    { id: "qa", label: "QA", icon: FlaskConical },
    { id: "system_health", label: "System Health", icon: Cpu },
  ];

  return (
    <aside className="w-56 bg-[#0B0F17] border-r border-[#18202d] flex flex-col justify-between p-4 h-[calc(100vh-3.5rem)] sticky top-14 select-none shrink-0">
      <div className="flex flex-col gap-6">
        {/* Logo Card Header */}
        <div
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-3 px-1 py-1 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-950 via-slate-900 to-sky-950 border border-sky-500/30 flex items-center justify-center text-sky-400 shadow-md shadow-cyan-950/50 group-hover:border-sky-400/60 transition-colors">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M12 8v4" />
              <path d="M12 16h.01" />
            </svg>
          </div>
          <div>
            <div className="font-bold text-sm text-slate-100 leading-tight group-hover:text-white transition-colors">
              Consensus<br />Dev
            </div>
            <div className="text-[11px] font-mono text-[#787777] mt-0.5">
              v2.4.0-stable
            </div>
          </div>
        </div>

        {/* Section Anchors */}
        <nav className="flex flex-col gap-1">
          {sections.map((sec) => {
            const Icon = sec.icon;
            const isActive = activeSection === sec.id;
            return (
              <button
                key={sec.id}
                type="button"
                onClick={() => navigateToSection(sec.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all text-left cursor-pointer",
                  isActive
                    ? "bg-[#151C28] text-slate-100 font-semibold border-l-2 border-l-slate-200 shadow-sm"
                    : "text-[#787777] hover:text-slate-200 hover:bg-[#151C28]/50"
                )}
              >
                <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-slate-100" : "text-[#787777]")} />
                <span>{sec.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Links */}
      <div className="flex flex-col gap-1 border-t border-[#18202d] pt-4">
        <button
          type="button"
          onClick={() => navigateToSection("architecture")}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-[#787777] hover:text-slate-200 hover:bg-[#151C28]/50 transition-colors w-full text-left cursor-pointer"
        >
          <FileText className="w-4 h-4" />
          <span>Documentation</span>
        </button>
        <button
          type="button"
          onClick={() => navigate("/logs")}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-[#787777] hover:text-slate-200 hover:bg-[#151C28]/50 transition-colors w-full text-left cursor-pointer"
        >
          <Terminal className="w-4 h-4" />
          <span>Terminal</span>
        </button>
      </div>
    </aside>
  );
}
