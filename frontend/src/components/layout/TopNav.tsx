import { NavLink, useNavigate } from "react-router-dom";
import { Bell, Settings, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function TopNav() {
  const navigate = useNavigate();

  const navLinks = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/pull-requests", label: "Pull Requests" },
    { to: "/agents", label: "Agents" },
    { to: "/pipelines", label: "Pipelines" },
    { to: "/logs", label: "Logs" },
  ];

  return (
    <header className="h-14 bg-[#0B0F17] border-b border-[#18202d] px-5 flex items-center justify-between sticky top-0 z-40 select-none">
      {/* Brand Logo */}
      <div
        onClick={() => navigate("/pull-requests")}
        className="flex items-center gap-3 cursor-pointer group"
      >
        <div className="w-7 h-7 rounded-md bg-gradient-to-br from-cyan-500/20 via-sky-500/10 to-indigo-500/30 border border-sky-400/40 flex items-center justify-center text-sky-300 shadow-sm shadow-sky-500/10">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="font-extrabold tracking-wider text-sm text-slate-100 uppercase">
            CONSENSUS DEV
          </span>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="flex items-center gap-1">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                "relative px-3.5 py-1.5 text-xs font-medium rounded-md transition-all",
                isActive
                  ? "text-slate-100 font-semibold after:absolute after:bottom-[-13px] after:left-3 after:right-3 after:h-[2px] after:bg-slate-200"
                  : "text-[#787777] hover:text-slate-200 hover:bg-[#151C28]/60"
              )
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      {/* Action Icons */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => navigate("/pipelines")}
          className="w-8 h-8 rounded-lg text-[#787777] hover:text-slate-200 hover:bg-[#151C28] flex items-center justify-center transition-colors cursor-pointer"
          title="Microservices Topology"
        >
          <Share2 className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => navigate("/logs")}
          className="relative w-8 h-8 rounded-lg text-[#787777] hover:text-slate-200 hover:bg-[#151C28] flex items-center justify-center transition-colors cursor-pointer"
          title="Notifications & Gate Alerts"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-1.5 h-1.5 bg-sky-400 rounded-full ring-2 ring-[#0B0F17]" />
        </button>
        <button
          type="button"
          onClick={() => navigate("/agents")}
          className="w-8 h-8 rounded-lg text-[#787777] hover:text-slate-200 hover:bg-[#151C28] flex items-center justify-center transition-colors cursor-pointer"
          title="Reviewer Agent Settings"
        >
          <Settings className="w-4 h-4" />
        </button>

        <div className="h-4 w-[1px] bg-[#1d2536] mx-1" />

        {/* User Avatar */}
        <div className="flex items-center gap-2 pl-1 cursor-pointer">
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-sky-600 to-indigo-500 border border-sky-400/40 flex items-center justify-center text-[10px] font-bold text-white shadow-sm overflow-hidden">
            <span>AS</span>
          </div>
        </div>
      </div>
    </header>
  );
}
