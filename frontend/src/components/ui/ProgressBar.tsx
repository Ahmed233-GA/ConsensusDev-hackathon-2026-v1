import { cn } from "@/lib/utils";

export interface ProgressBarProps {
  value: number; // 0 to 100
  max?: number;
  className?: string;
  barClassName?: string;
  variant?: "default" | "segmented" | "danger" | "warning";
  segments?: Array<{
    value: number; // percentage of total
    colorClass: string;
    label?: string;
  }>;
}

export function ProgressBar({
  value,
  max = 100,
  className,
  barClassName,
  variant = "default",
  segments,
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  if (variant === "segmented" && segments && segments.length > 0) {
    return (
      <div
        className={cn(
          "w-full h-1.5 bg-[#18202d] rounded-full overflow-hidden flex gap-0.5",
          className
        )}
      >
        {segments.map((seg, idx) => (
          <div
            key={idx}
            style={{ width: `${Math.max(seg.value, 0)}%` }}
            className={cn("h-full transition-all duration-300", seg.colorClass)}
            title={seg.label}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "w-full h-1.5 bg-[#1a2232] rounded-full overflow-hidden",
        className
      )}
    >
      <div
        style={{ width: `${percentage}%` }}
        className={cn(
          "h-full bg-slate-200 rounded-full transition-all duration-300",
          variant === "danger" && "bg-[#f87171]",
          variant === "warning" && "bg-[#fb923c]",
          barClassName
        )}
      />
    </div>
  );
}
