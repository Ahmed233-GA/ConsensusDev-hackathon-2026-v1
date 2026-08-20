import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "inverted" | "outlined" | "ghost" | "danger";
  size?: "sm" | "md" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "secondary", size = "md", children, ...props }, ref) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-400 disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer";

    const variantStyles = {
      primary:
        "bg-slate-100 text-slate-950 hover:bg-white active:bg-slate-200 shadow-sm font-semibold",
      secondary:
        "bg-[#151C28] text-slate-200 border border-[#20293a] hover:bg-[#1a2332] hover:border-[#2d3a52] active:bg-[#121822]",
      inverted:
        "bg-white text-slate-900 hover:bg-slate-100 active:bg-slate-200 font-semibold",
      outlined:
        "bg-transparent text-slate-200 border border-[#2d3748] hover:bg-[#151C28] hover:border-[#4a5568]",
      ghost:
        "bg-transparent text-slate-300 hover:bg-[#151C28] hover:text-white",
      danger:
        "bg-[#261014] text-red-400 border border-[#7A1F2B] hover:bg-[#34151b] active:bg-[#1c0d11]",
    };

    const sizeStyles = {
      sm: "h-7 px-2.5 text-xs rounded-md gap-1.5",
      md: "h-9 px-3.5 text-sm rounded-lg gap-2",
      lg: "h-11 px-5 text-base rounded-lg gap-2.5",
      icon: "h-8 w-8 rounded-lg p-0",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
