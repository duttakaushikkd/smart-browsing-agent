"use client";

import { cn } from "@/lib/utils";

type LoaderProps = {
  className?: string;
};

export function Loader({ className }: LoaderProps) {
  return (
    <div className={cn("flex items-center gap-2 text-sm text-slate-300", className)} aria-label="Loading response">
      <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-cyan-400/90 shadow-[0_0_16px_rgba(34,211,238,0.55)]" />
      <span
        className="h-2.5 w-2.5 animate-pulse rounded-full bg-sky-400/90 shadow-[0_0_16px_rgba(96,165,250,0.55)]"
        style={{ animationDelay: "120ms" }}
      />
      <span
        className="h-2.5 w-2.5 animate-pulse rounded-full bg-violet-400/90 shadow-[0_0_16px_rgba(167,139,250,0.55)]"
        style={{ animationDelay: "240ms" }}
      />
    </div>
  );
}
