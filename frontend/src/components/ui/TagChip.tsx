import * as React from "react";
import { cn } from "@/lib/utils";

export interface TagChipProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  variant?: "default" | "active" | "neutral" | "mono";
}

export function TagChip({
  className,
  icon,
  variant = "default",
  children,
  ...props
}: TagChipProps) {
  const variantStyles = {
    default: "bg-[#151C28] text-slate-300 border border-[#202a3c] hover:border-[#2d3b54]",
    active: "bg-[#1f2a3e] text-white border border-slate-400/40",
    neutral: "bg-[#111622] text-[#8e9bb0] border border-[#1b2333]",
    mono: "bg-[#10141e] text-slate-300 border border-[#1d2536] font-mono text-xs",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors select-none",
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {icon && <span className="text-[#8e9bb0] flex items-center justify-center shrink-0">{icon}</span>}
      <span>{children}</span>
    </div>
  );
}
