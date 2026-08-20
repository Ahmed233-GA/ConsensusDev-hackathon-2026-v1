import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsContextType {
  value: string;
  onChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextType | undefined>(undefined);

export interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}

export function Tabs({ value, onValueChange, children, className }: TabsProps) {
  return (
    <TabsContext.Provider value={{ value, onChange: onValueChange }}>
      <div className={cn("w-full flex flex-col", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export interface TabsListProps {
  children: React.ReactNode;
  className?: string;
}

export function TabsList({ children, className }: TabsListProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-1 border-b border-[#1d2536] bg-transparent overflow-x-auto select-none",
        className
      )}
    >
      {children}
    </div>
  );
}

export interface TabsTriggerProps {
  value: string;
  children: React.ReactNode;
  className?: string;
  badge?: React.ReactNode;
}

export function TabsTrigger({ value, children, className, badge }: TabsTriggerProps) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("TabsTrigger must be used inside Tabs");

  const isActive = ctx.value === value;

  return (
    <button
      type="button"
      onClick={() => ctx.onChange(value)}
      className={cn(
        "relative px-4 py-2.5 text-xs font-medium transition-all flex items-center gap-2 cursor-pointer outline-none whitespace-nowrap",
        isActive
          ? "text-slate-100 font-semibold bg-[#151C28] rounded-t-lg border-t border-x border-[#1d2536] after:absolute after:bottom-[-1px] after:left-0 after:right-0 after:h-[2px] after:bg-slate-100"
          : "text-[#787777] hover:text-slate-300 hover:bg-[#111722]/50",
        className
      )}
    >
      <span>{children}</span>
      {badge}
    </button>
  );
}

export interface TabsContentProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const ctx = React.useContext(TabsContext);
  if (!ctx) throw new Error("TabsContent must be used inside Tabs");

  if (ctx.value !== value) return null;

  return (
    <div className={cn("pt-4 animate-in fade-in-50 duration-150", className)}>
      {children}
    </div>
  );
}
