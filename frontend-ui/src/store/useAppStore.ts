import { create } from "zustand";
import {
  clearStoredPlannerSession,
  loadStoredPlannerSession,
  saveStoredPlannerSession
} from "@/services/plannerSessionStorage";
import { PlannerStreamClient } from "@/services/plannerSocket";
import { formatPlannerEvent, isTerminalPlannerState } from "@/services/plannerEvents";
import { getPlannerApiBaseUrl, plannerApi } from "@/services/plannerApi";
import type {
  AgentState,
  AgentStatusResponse,
  ConversationEntry,
  PlannerConnectionState,
  PlannerStreamEvent,
  ResponseStatus
} from "@/types";

type AppState = {
  query: string;
  status: ResponseStatus;
  error: string | null;
  history: ConversationEntry[];
  activeResponse: ConversationEntry | null;
  activeConversationId: string | null;
  activeSessionId: string | null;
  plannerState: AgentState | null;
  connectionState: PlannerConnectionState;
  apiBaseUrl: string;
  setQuery: (query: string) => void;
  clearError: () => void;
  selectConversation: (id: string) => void;
  submit: () => Promise<void>;
  cancelActiveSession: () => Promise<void>;
  continueActiveSession: (userInput?: string) => Promise<void>;
  restoreSession: () => Promise<void>;
  refreshActiveStatus: () => Promise<void>;
};

let streamClient: PlannerStreamClient | null = null;

function createId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function plannerStatusToResponseStatus(state: AgentState): ResponseStatus {
  const normalized = String(state).toLowerCase();
  if (normalized === "completed") return "success";
  if (normalized === "failed" || normalized === "cancelled") return "error";
  return "loading";
}

function responseFromStatus(status: AgentStatusResponse) {
  if (status.final_result) return status.final_result;
  const timeline = status.timeline.map((event) => event.message).filter(Boolean);
  if (status.plan_summary) timeline.push(status.plan_summary);
  if (status.error) timeline.push(`Error: ${status.error}`);
  return timeline.join("\n\n");
}

function responseFromEvents(events: PlannerStreamEvent[], fallback = "") {
  const completion = [...events].reverse().find((event) => event.event === "completion");
  const finalResult = completion?.payload?.final_result;
  if (typeof finalResult === "string" && finalResult.trim()) return finalResult;

  const rendered = events
    .filter((event) => event.event !== "heartbeat")
    .map(formatPlannerEvent)
    .join("\n\n");

  return rendered || fallback;
}

function upsertConversation(
  history: ConversationEntry[],
  entry: ConversationEntry
): ConversationEntry[] {
  const existing = history.findIndex((item) => item.id === entry.id);
  if (existing === -1) return [entry, ...history];
  return history.map((item) => (item.id === entry.id ? entry : item));
}

function disconnectStream() {
  streamClient?.disconnect();
  streamClient = null;
}

function connectStream(sessionId: string) {
  disconnectStream();
  streamClient = new PlannerStreamClient({
    streamUrl: plannerApi.getStreamUrl(sessionId),
    onConnectionChange: (connectionState) => useAppStore.setState({ connectionState }),
    onError: (message) => useAppStore.setState({ error: message }),
    onEvent: (event) => useAppStore.getState().applyPlannerEvent(event)
  });
  streamClient.connect();
}

type InternalAppState = AppState & {
  applyPlannerEvent: (event: PlannerStreamEvent) => void;
  applyPlannerStatus: (status: AgentStatusResponse, conversationId?: string) => void;
};

export const useAppStore = create<InternalAppState>((set, get) => ({
  query: "",
  status: "idle",
  error: null,
  history: [],
  activeResponse: null,
  activeConversationId: null,
  activeSessionId: null,
  plannerState: null,
  connectionState: "disconnected",
  apiBaseUrl: getPlannerApiBaseUrl(),

  setQuery: (query) => set({ query }),

  clearError: () => set({ error: null }),

  selectConversation: (id) =>
    set((state) => {
      const selected = state.history.find((item) => item.id === id) ?? null;

      return {
        activeConversationId: id,
        activeResponse: selected ?? state.activeResponse,
        activeSessionId: selected?.sessionId ?? state.activeSessionId,
        plannerState: selected?.plannerState ?? state.plannerState,
        query: selected?.query ?? state.query,
        error: null
      };
    }),

  submit: async () => {
    const query = get().query.trim();

    if (!query) {
      set({ error: "Please enter a browsing goal before submitting." });
      return;
    }

    disconnectStream();
    const id = createId();
    const createdAt = new Date().toISOString();
    const draft: ConversationEntry = {
      id,
      query,
      response: "Starting planner session...",
      createdAt,
      events: []
    };

    set({
      status: "loading",
      error: null,
      activeConversationId: id,
      activeResponse: draft,
      connectionState: "connecting"
    });

    try {
      const started = await plannerApi.start({ goal: query, metadata: { source: "frontend-ui" } });
      const entry: ConversationEntry = {
        ...draft,
        sessionId: started.session_id,
        plannerState: started.state,
        response: `Planner session started.\n\nState: ${String(started.state).toUpperCase()}`
      };

      saveStoredPlannerSession({
        sessionId: started.session_id,
        goal: query,
        conversationId: id,
        createdAt
      });

      set((state) => ({
        query: "",
        activeSessionId: started.session_id,
        plannerState: started.state,
        activeResponse: entry,
        history: upsertConversation(state.history, entry)
      }));

      connectStream(started.session_id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Planner service is unavailable.";
      disconnectStream();
      set({
        status: "error",
        error: message,
        connectionState: "disconnected",
        activeResponse: { ...draft, response: message }
      });
    }
  },

  cancelActiveSession: async () => {
    const sessionId = get().activeSessionId;
    if (!sessionId) return;

    try {
      const cancelled = await plannerApi.cancel(sessionId);
      clearStoredPlannerSession(sessionId);
      disconnectStream();
      set((state) => {
        const active = state.activeResponse;
        const updated = active
          ? {
              ...active,
              plannerState: cancelled.state,
              response: `${active.response}\n\nSession cancelled.`
            }
          : active;
        return {
          status: "error",
          plannerState: cancelled.state,
          connectionState: "disconnected",
          activeResponse: updated,
          history: updated ? upsertConversation(state.history, updated) : state.history
        };
      });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unable to cancel planner session." });
    }
  },

  continueActiveSession: async (userInput) => {
    const sessionId = get().activeSessionId;
    if (!sessionId) return;

    try {
      const status = await plannerApi.continue(sessionId, { user_input: userInput ?? null });
      get().applyPlannerStatus(status);
      if (!isTerminalPlannerState(status.state)) connectStream(sessionId);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unable to continue planner session." });
    }
  },

  restoreSession: async () => {
    const stored = loadStoredPlannerSession();
    if (!stored) return;

    try {
      const status = await plannerApi.status(stored.sessionId);
      get().applyPlannerStatus(status, stored.conversationId);
      if (!isTerminalPlannerState(status.state)) connectStream(stored.sessionId);
      else clearStoredPlannerSession(stored.sessionId);
    } catch (error) {
      clearStoredPlannerSession(stored.sessionId);
      set({
        connectionState: "disconnected",
        error: error instanceof Error ? error.message : "Unable to restore planner session."
      });
    }
  },

  refreshActiveStatus: async () => {
    const sessionId = get().activeSessionId;
    if (!sessionId) return;

    try {
      const status = await plannerApi.status(sessionId);
      get().applyPlannerStatus(status);
    } catch (error) {
      set({ error: error instanceof Error ? error.message : "Unable to refresh planner status." });
    }
  },

  applyPlannerEvent: (event) =>
    set((state) => {
      const active = state.activeResponse;
      if (!active) return state;

      const events = [...(active.events ?? []), event].slice(-100);
      const plannerState = event.state ?? active.plannerState ?? state.plannerState ?? undefined;
      const updated: ConversationEntry = {
        ...active,
        plannerState,
        currentStep: event.step ?? active.currentStep,
        events,
        response: responseFromEvents(events, active.response)
      };
      const terminal = isTerminalPlannerState(plannerState);

      if (terminal && active.sessionId) {
        clearStoredPlannerSession(active.sessionId);
        disconnectStream();
      }

      return {
        status: terminal && plannerState ? plannerStatusToResponseStatus(plannerState) : "loading",
        error: event.event === "error" ? event.message ?? "Planner error." : state.error,
        plannerState: plannerState ?? null,
        connectionState: terminal ? "disconnected" : state.connectionState,
        activeResponse: updated,
        history: upsertConversation(state.history, updated)
      };
    }),

  applyPlannerStatus: (status, conversationId) =>
    set((state) => {
      const id = conversationId ?? state.activeConversationId ?? createId();
      const existing =
        state.history.find((item) => item.id === id) ??
        state.activeResponse ??
        ({
          id,
          sessionId: status.session_id,
          query: status.goal,
          response: "",
          createdAt: new Date().toISOString(),
          events: []
        } satisfies ConversationEntry);

      const updated: ConversationEntry = {
        ...existing,
        id,
        sessionId: status.session_id,
        query: status.goal,
        response: responseFromStatus(status),
        plannerState: status.state,
        currentStep: status.current_step
      };
      const terminal = isTerminalPlannerState(status.state);

      if (terminal) clearStoredPlannerSession(status.session_id);

      return {
        status: plannerStatusToResponseStatus(status.state),
        error: status.error,
        activeSessionId: status.session_id,
        activeConversationId: id,
        plannerState: status.state,
        activeResponse: updated,
        history: upsertConversation(state.history, updated),
        connectionState: terminal ? "disconnected" : state.connectionState
      };
    })
}));

export function useActiveConversation() {
  return useAppStore((state) => state.activeResponse);
}
