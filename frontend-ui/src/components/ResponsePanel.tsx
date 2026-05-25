"use client";

import { Check, Copy, RefreshCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useAutoScroll } from "@/hooks/useAutoScroll";
import { useTypewriter } from "@/hooks/useTypewriter";
import { cn } from "@/lib/utils";
import type { ConversationEntry, ResponseStatus } from "@/types";
import { EmptyState } from "./EmptyState";
import { Loader } from "./Loader";
import { MessageBubble } from "./MessageBubble";

type ResponsePanelProps = {
  conversation: ConversationEntry | null;
  loading: boolean;
  status: ResponseStatus;
  error: string | null;
  onPromptSelect: (query: string) => void;
};

export function ResponsePanel({ conversation, loading, status, error, onPromptSelect }: ResponsePanelProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const containerRef = useRef<HTMLDivElement>(null);
  const animatedResponse = useTypewriter({
    text: conversation?.response ?? "",
    speed: 10,
    enabled: Boolean(conversation && !loading)
  });

  const responseText = useMemo(() => {
    if (!conversation) return "";
    return animatedResponse || conversation.response;
  }, [animatedResponse, conversation]);

  useAutoScroll(containerRef, [conversation?.id, conversation?.response, error, loading]);

  useEffect(() => {
    setCopyState("idle");
  }, [conversation?.id]);

  const handleCopy = async () => {
    if (!conversation?.response) return;
    try {
      await navigator.clipboard.writeText(conversation.response);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 1400);
    } catch {
      setCopyState("idle");
    }
  };

  if (!conversation && !loading && !error) {
    return <EmptyState onPromptSelect={onPromptSelect} />;
  }

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 shadow-glow backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4 border-b border-white/10 px-4 py-4 sm:px-6">
        <div>
          <h2 className="text-base font-semibold text-white">AI Response</h2>
          <p className="mt-1 text-sm text-slate-400">Stream-ready response area with clipboard support and history-aware rendering.</p>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          disabled={!conversation?.response}
          className={cn(
            "inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-medium transition duration-200",
            copyState === "copied"
              ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200"
              : "border-white/10 bg-white/5 text-slate-200 hover:bg-white/10",
            "disabled:cursor-not-allowed disabled:opacity-40"
          )}
        >
          {copyState === "copied" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copyState === "copied" ? "Copied" : "Copy response"}
        </button>
      </div>

      <div ref={containerRef} className="max-h-[70vh] overflow-auto px-4 py-5 sm:px-6">
        {conversation ? (
          <div className="space-y-4">
            <MessageBubble role="user" content={conversation.query} />
            {loading ? (
              <div className="rounded-[1.6rem] border border-white/10 bg-white/5 p-5">
                <div className="mb-4 flex items-center gap-3">
                  <Loader />
                  <span className="text-sm text-slate-300">Searching the web and composing a response...</span>
                </div>
                <div className="space-y-3">
                  <div className="h-4 w-4/5 animate-pulse rounded-full bg-white/10" />
                  <div className="h-4 w-11/12 animate-pulse rounded-full bg-white/10" />
                  <div className="h-4 w-3/4 animate-pulse rounded-full bg-white/10" />
                </div>
              </div>
            ) : conversation.response ? (
              <MessageBubble role="assistant" content={responseText} animate />
            ) : null}
          </div>
        ) : loading ? (
          <div className="rounded-[1.6rem] border border-white/10 bg-white/5 p-5">
            <div className="mb-4 flex items-center gap-3">
              <Loader />
              <span className="text-sm text-slate-300">Searching the web and composing a response...</span>
            </div>
            <div className="space-y-3">
              <div className="h-4 w-4/5 animate-pulse rounded-full bg-white/10" />
              <div className="h-4 w-11/12 animate-pulse rounded-full bg-white/10" />
              <div className="h-4 w-3/4 animate-pulse rounded-full bg-white/10" />
            </div>
          </div>
        ) : null}

        {!loading && error ? (
          <div className="mt-4 rounded-[1.5rem] border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
            <p className="font-medium">Something went wrong</p>
            <p className="mt-1 leading-6 text-rose-100/85">{error}</p>
            {status === "error" ? (
              <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-200">
                <div className="flex items-center gap-2 text-sm font-medium text-white">
                  <RefreshCcw className="h-4 w-4 text-cyan-300" />
                  Ready for another search
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Fix the issue above and try again. The interface will keep your layout intact while the backend recovers.
                </p>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
