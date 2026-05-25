"use client";

import { ShieldCheck, Sparkles } from "lucide-react";

type HeaderProps = {
  apiBaseUrl: string;
};

export function Header({ apiBaseUrl }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-slate-950/70 backdrop-blur-2xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 via-sky-400 to-violet-400 text-slate-950 shadow-[0_10px_30px_rgba(34,211,238,0.3)]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white sm:text-xl">Smart Browsing Agent</h1>
            <p className="text-xs text-slate-400 sm:text-sm">AI browser frontend with a clean search-and-answer workspace</p>
          </div>
        </div>

        <div className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-200 sm:flex">
          <ShieldCheck className="h-3.5 w-3.5" />
          Connected to {apiBaseUrl}
        </div>
      </div>
    </header>
  );
}
