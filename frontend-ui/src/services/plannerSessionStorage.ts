const STORAGE_KEY = "smart-browsing-agent.active-session";

export type StoredPlannerSession = {
  sessionId: string;
  goal: string;
  conversationId: string;
  createdAt: string;
};

export function loadStoredPlannerSession(): StoredPlannerSession | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<StoredPlannerSession>;
    if (!parsed.sessionId || !parsed.goal || !parsed.conversationId || !parsed.createdAt) {
      return null;
    }
    return parsed as StoredPlannerSession;
  } catch {
    return null;
  }
}

export function saveStoredPlannerSession(session: StoredPlannerSession) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredPlannerSession(sessionId?: string) {
  if (typeof window === "undefined") return;
  if (!sessionId) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }

  const existing = loadStoredPlannerSession();
  if (existing?.sessionId === sessionId) {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}
