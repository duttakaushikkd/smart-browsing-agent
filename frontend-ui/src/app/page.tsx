"use client";

import { useEffect } from "react";
import { Header } from "@/components/Header";
import { ResponsePanel } from "@/components/ResponsePanel";
import { SearchBar } from "@/components/SearchBar";
import { Sidebar } from "@/components/Sidebar";
import { useAppStore, useActiveConversation } from "@/store/useAppStore";

export default function Page() {
  const query = useAppStore((state) => state.query);
  const status = useAppStore((state) => state.status);
  const error = useAppStore((state) => state.error);
  const history = useAppStore((state) => state.history);
  const activeConversationId = useAppStore((state) => state.activeConversationId);
  const apiBaseUrl = useAppStore((state) => state.apiBaseUrl);
  const cancelActiveSession = useAppStore((state) => state.cancelActiveSession);
  const restoreSession = useAppStore((state) => state.restoreSession);
  const setQuery = useAppStore((state) => state.setQuery);
  const submit = useAppStore((state) => state.submit);
  const selectConversation = useAppStore((state) => state.selectConversation);

  const activeConversation = useActiveConversation();

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  useEffect(() => {
    if (error && status !== "loading") {
      const timer = window.setTimeout(() => useAppStore.getState().clearError(), 5000);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [error, status]);

  return (
    <div className="min-h-screen">
      <Header apiBaseUrl={apiBaseUrl} />

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
          <Sidebar
            history={history}
            activeConversationId={activeConversationId}
            onSelect={selectConversation}
            apiBaseUrl={apiBaseUrl}
          />

          <section className="min-w-0 space-y-6">
            <SearchBar
              value={query}
              onChange={(value) => {
                setQuery(value);
                if (error) useAppStore.getState().clearError();
              }}
              onSubmit={submit}
              onCancel={() => void cancelActiveSession()}
              loading={status === "loading"}
            />

            <ResponsePanel
              conversation={activeConversation}
              loading={status === "loading"}
              status={status}
              error={error}
              onPromptSelect={(value) => {
                setQuery(value);
                useAppStore.getState().clearError();
              }}
            />
          </section>
        </div>
      </main>
    </div>
  );
}
