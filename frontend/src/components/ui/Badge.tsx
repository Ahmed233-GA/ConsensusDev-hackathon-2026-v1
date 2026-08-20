import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "approved" | "rejected" | "pending" | "pass" | "fail" | "high" | "med" | "critical" | "mono";
}

export function Badge({ className, variant = "default", children, ...props }: BadgeProps) {
  const variantStyles = {
    default: "bg-[#1e2738] text-slate-300 border border-[#2d3a50]",
    approved: "bg-transparent text-slate-100 border border-slate-400/80 tracking-wider text-[11px] font-semibold uppercase px-3 py-0.5 rounded-full",
    rejected: "bg-[#261014] text-red-400 border border-[#7A1F2B] tracking-wider text-[11px] font-semibold uppercase px-3 py-0.5 rounded-full",
    pending: "bg-[#221b0a] text-yellow-300 border border-[#C9A227] tracking-wider text-[11px] font-semibold uppercase px-3 py-0.5 rounded-full",
    pass: "bg-[#18202d] text-slate-100 border border-[#2d3748] text-[11px] font-bold tracking-wider px-2 py-0.5 rounded",
    fail: "bg-[#261014] text-red-400 border border-[#7A1F2B] text-[11px] font-bold tracking-wider px-2 py-0.5 rounded",
    high: "bg-[#27170c] text-[#fb923c] border border-[#C77A2B] font-mono font-semibold text-[11px] tracking-wider px-2.5 py-0.5 rounded",
    med: "bg-[#221b0a] text-[#facc15] border border-[#C9A227] font-mono font-semibold text-[11px] tracking-wider px-2.5 py-0.5 rounded",
    critical: "bg-[#1c0d11] text-[#f87171] border border-[#7A1F2B] font-mono font-semibold text-[11px] tracking-wider px-2.5 py-0.5 rounded",
    mono: "bg-[#121822] text-slate-300 border border-[#1e2738] font-mono text-xs px-2 py-0.5 rounded",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center font-medium transition-colors select-none",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
