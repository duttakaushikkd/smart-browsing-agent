"use client";

import { ArrowRight, LoaderCircle, Search } from "lucide-react";
import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

type SearchBarProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
};

export function SearchBar({
  value,
  onChange,
  onSubmit,
  loading = false,
  placeholder = "Ask the AI browser anything...",
  autoFocus = true
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
      className="sticky top-4 z-30 rounded-[2rem] border border-white/10 bg-slate-950/75 p-3 shadow-glow backdrop-blur-2xl"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-3 rounded-[1.5rem] border border-white/10 bg-white/5 px-4 py-3 transition focus-within:border-cyan-400/40 focus-within:bg-white/10">
          <Search className="h-5 w-5 shrink-0 text-slate-400" />
          <input
            ref={inputRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder={placeholder}
            className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500 sm:text-base"
            aria-label="Search query"
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !value.trim()}
          className={cn(
            "inline-flex items-center justify-center gap-2 rounded-[1.5rem] px-5 py-3 text-sm font-medium transition duration-200",
            "bg-gradient-to-r from-cyan-400 via-sky-400 to-violet-400 text-slate-950 shadow-[0_14px_50px_rgba(34,211,238,0.25)] hover:-translate-y-0.5 hover:shadow-[0_18px_60px_rgba(34,211,238,0.35)]",
            "disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
          )}
        >
          {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          <span>{loading ? "Thinking..." : "Submit"}</span>
        </button>
      </div>
    </form>
  );
}
