import * as React from "react";
import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-[32rem] w-full resize-y rounded-xl border border-white/[0.07] bg-[#0f1622] p-5 font-mono text-[0.8rem] leading-6 text-slate-200/85 shadow-[inset_0_1px_0_rgba(255,255,255,0.018)] outline-none focus:border-white/12 focus:ring-2 focus:ring-ring/25",
        className
      )}
      {...props}
    />
  );
}
