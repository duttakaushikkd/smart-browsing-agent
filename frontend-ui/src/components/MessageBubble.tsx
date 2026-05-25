"use client";

import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MessageBubbleProps = {
  role: "user" | "assistant";
  content: string;
  animate?: boolean;
};

export function MessageBubble({ role, content, animate }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={cn("rounded-[1.6rem] border p-4 sm:p-5", animate && "animate-rise", isUser ? "border-cyan-400/20 bg-cyan-500/10" : "border-white/10 bg-white/5")}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className={cn("text-xs font-medium uppercase tracking-[0.2em]", isUser ? "text-cyan-200" : "text-slate-300")}>
          {isUser ? "You" : "Assistant"}
        </span>
        <span className="text-[11px] text-slate-500">{isUser ? "Prompt" : "AI response"}</span>
      </div>

      {isUser ? (
        <p className="whitespace-pre-wrap text-sm leading-7 text-cyan-50">{content}</p>
      ) : (
        <div className="prose prose-invert max-w-none prose-p:leading-7 prose-li:leading-7 prose-a:text-cyan-300 prose-strong:text-white">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
