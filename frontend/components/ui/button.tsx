import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
}

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border font-medium transition-all focus:outline-none focus:ring-2 focus:ring-ring disabled:pointer-events-none disabled:opacity-50",
        size === "sm" ? "h-8 px-3 text-sm" : "h-10 px-4 text-sm",
        variant === "primary" && "border-emerald-200/10 bg-emerald-200/80 text-slate-950 shadow-[0_8px_20px_rgba(0,0,0,0.14)] hover:bg-emerald-100/85",
        variant === "secondary" && "border-white/[0.075] bg-white/[0.035] text-foreground hover:border-white/12 hover:bg-white/[0.055]",
        variant === "ghost" && "border-transparent bg-transparent text-muted-foreground hover:bg-white/[0.035] hover:text-foreground",
        variant === "danger" && "border-destructive bg-destructive text-destructive-foreground hover:bg-destructive/90",
        className
      )}
      {...props}
    />
  );
}
