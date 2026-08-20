import { Outlet } from "react-router-dom";
import { TopNav } from "@/components/layout/TopNav";
import { Sidebar } from "@/components/layout/Sidebar";

export function AppShell() {
  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-200 flex flex-col">
      {/* Top Navbar */}
      <TopNav />

      {/* Main Content Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar />

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto min-h-[calc(100vh-3.5rem)] bg-[#0B0F17]">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
