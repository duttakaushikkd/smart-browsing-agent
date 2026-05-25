import { create } from "zustand";
import { getApiBaseUrl, submitQuery } from "@/services/api";
import type { ConversationEntry, ResponseStatus } from "@/types";

type AppState = {
  query: string;
  status: ResponseStatus;
  error: string | null;
  history: ConversationEntry[];
  activeResponse: ConversationEntry | null;
  activeConversationId: string | null;
  apiBaseUrl: string;
  setQuery: (query: string) => void;
  clearError: () => void;
  selectConversation: (id: string) => void;
  submit: () => Promise<void>;
};

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export const useAppStore = create<AppState>((set, get) => ({
  query: "",
  status: "idle",
  error: null,
  history: [],
  activeResponse: null,
  activeConversationId: null,
  apiBaseUrl: getApiBaseUrl(),

  setQuery: (query) => set({ query }),

  clearError: () => set({ error: null }),

  selectConversation: (id) =>
    set((state) => {
      const selected = state.history.find((item) => item.id === id) ?? null;

      return {
        activeConversationId: id,
        activeResponse: selected ?? state.activeResponse,
        query: selected?.query ?? state.query,
        error: null
      };
    }),

  submit: async () => {
    const query = get().query.trim();

    if (!query) {
      set({ error: "Please enter a query before submitting." });
      return;
    }

    const id = createId();
    const createdAt = new Date().toISOString();
    const draft: ConversationEntry = {
      id,
      query,
      response: "",
      createdAt
    };

    set({ status: "loading", error: null, activeConversationId: id, activeResponse: draft });

    try {
      const result = await submitQuery({ query });

      const entry: ConversationEntry = {
        id,
        query,
        response: result.response,
        createdAt
      };

      set((state) => ({
        status: "success",
        error: null,
        query: "",
        history: [entry, ...state.history],
        activeConversationId: id,
        activeResponse: entry
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Something went wrong. Please try again.";
      set({ status: "error", error: message, activeResponse: draft });
    }
  }
}));

export function useActiveConversation() {
  return useAppStore((state) => state.activeResponse);
}
