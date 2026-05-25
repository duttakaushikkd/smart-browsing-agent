"use client";

import { Search, Sparkles } from "lucide-react";

type EmptyStateProps = {
  onPromptSelect: (query: string) => void;
};

const suggestions = [
  "Find the best laptops under $1000",
  "Compare the top AI browsers in 2026",
  "Summarize the latest React 19 updates"
];

export function EmptyState({ onPromptSelect }: EmptyStateProps) {
  return (
    <div className="flex min-h-[480px] flex-col items-center justify-center rounded-[2rem] border border-white/10 bg-white/5 px-6 py-12 text-center shadow-glow backdrop-blur-xl">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full border border-white/10 bg-white/10">
        <Sparkles className="h-8 w-8 text-cyan-300" />
      </div>
      <h2 className="text-2xl font-semibold tracking-tight text-white">Ask anything and let the browser think for you.</h2>
      <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
        Search, compare, summarize, and explore with a clean AI-native workspace designed for fast iteration.
      </p>

      <div className="mt-8 grid w-full gap-3 sm:grid-cols-3">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onPromptSelect(suggestion)}
            className="group flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-left text-sm text-slate-200 transition duration-200 hover:-translate-y-0.5 hover:border-cyan-400/30 hover:bg-white/10"
          >
            <Search className="h-4 w-4 shrink-0 text-cyan-300 transition group-hover:scale-110" />
            <span>{suggestion}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
