import * as React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "subtle" | "active";
}

export function Card({ className, variant = "default", children, ...props }: CardProps) {
  const variantStyles = {
    default: "bg-[#151C28] border border-[#1d2536] rounded-xl text-slate-200",
    elevated: "bg-[#161e2b] border border-[#232d40] rounded-xl shadow-lg shadow-black/40 text-slate-200",
    subtle: "bg-[#0f141f] border border-[#1a2130] rounded-lg text-slate-300",
    active: "bg-[#172030] border border-slate-500/40 rounded-xl text-white",
  };

  return (
    <div className={cn(variantStyles[variant], className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-4 pb-2 flex items-center justify-between", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-sm font-semibold tracking-tight text-slate-100", className)} {...props}>
      {children}
    </h3>
  );
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-4 pt-2", className)} {...props}>
      {children}
    </div>
  );
}
