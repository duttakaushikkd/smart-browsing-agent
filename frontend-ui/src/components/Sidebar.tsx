"use client";

import { Clock3, History, Sparkles } from "lucide-react";
import type { ConversationEntry } from "@/types";
import { cn } from "@/lib/utils";

type SidebarProps = {
  history: ConversationEntry[];
  activeConversationId: string | null;
  onSelect: (id: string) => void;
  apiBaseUrl: string;
};

export function Sidebar({ history, activeConversationId, onSelect, apiBaseUrl }: SidebarProps) {
  const recent = history.slice(0, 6);

  return (
    <aside className="rounded-[2rem] border border-white/10 bg-white/5 p-4 shadow-glow backdrop-blur-xl lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:w-[320px] lg:overflow-hidden">
      <div className="flex items-center gap-3 border-b border-white/10 pb-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400/20 via-sky-400/20 to-violet-400/20">
          <Sparkles className="h-5 w-5 text-cyan-300" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">AI Browser</p>
          <p className="text-xs text-slate-400">Frontend connected to {apiBaseUrl}</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 rounded-[1.5rem] border border-white/10 bg-slate-950/55 p-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
          <History className="h-4 w-4" />
          Query history
        </div>

        {recent.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400">
            Your recent searches will appear here.
          </div>
        ) : (
          <div className="space-y-2">
            {recent.map((item) => {
              const active = item.id === activeConversationId;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelect(item.id)}
                  className={cn(
                    "w-full rounded-2xl border px-3 py-3 text-left transition duration-200 hover:-translate-y-0.5",
                    active ? "border-cyan-400/40 bg-cyan-400/10" : "border-white/10 bg-white/5 hover:bg-white/10"
                  )}
                >
                  <p className="max-h-10 overflow-hidden text-sm leading-5 text-white">{item.query}</p>
                  <div className="mt-2 flex items-center justify-between gap-2 text-[11px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock3 className="h-3 w-3" />
                      {new Date(item.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className="truncate text-slate-400">{item.response.slice(0, 30)}...</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-4 rounded-[1.5rem] border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
        <p className="font-medium text-white">Ready for streaming</p>
        <p className="mt-2 leading-6 text-slate-400">
          The API layer already supports a streaming-ready path, so we can add live token rendering without changing the UI structure.
        </p>
      </div>
    </aside>
  );
}
