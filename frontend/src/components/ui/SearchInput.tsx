import * as React from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, value, ...props }, ref) => {
    return (
      <div className="relative flex items-center w-full">
        <Search className="absolute left-3 w-4 h-4 text-[#787777] pointer-events-none" />
        <input
          ref={ref}
          type="text"
          value={value}
          className={cn(
            "w-full h-8 pl-9 pr-3 rounded-md bg-[#121722] border border-[#1e2637] text-xs text-slate-200 placeholder-[#787777] focus:outline-none focus:border-slate-400/50 transition-colors",
            className
          )}
          {...props}
        />
      </div>
    );
  }
);
SearchInput.displayName = "SearchInput";
