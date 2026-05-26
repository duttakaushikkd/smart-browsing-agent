import type { AgentState, PlannerEventName, PlannerStreamEvent } from "@/types";

const EVENT_NAMES = new Set<PlannerEventName>([
  "planner_update",
  "tool_execution",
  "observation",
  "screenshot",
  "recovery",
  "error",
  "completion",
  "heartbeat"
]);

const STATE_NAMES = new Set<string>([
  "idle",
  "planning",
  "executing",
  "observing",
  "replanning",
  "waiting_user",
  "completed",
  "failed",
  "cancelled",
  "IDLE",
  "PLANNING",
  "EXECUTING",
  "OBSERVING",
  "REPLANNING",
  "WAITING_USER",
  "COMPLETED",
  "FAILED",
  "CANCELLED"
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function normalizeEventName(raw: unknown, fallbackType: unknown): PlannerEventName {
  if (typeof raw === "string" && EVENT_NAMES.has(raw as PlannerEventName)) {
    return raw as PlannerEventName;
  }

  if (typeof fallbackType === "string") {
    if (fallbackType === "tool_result" || fallbackType === "action") return "tool_execution";
    if (fallbackType === "completion") return "completion";
    if (fallbackType === "error") return "error";
    if (fallbackType === "observation") return "observation";
  }

  return "planner_update";
}

function normalizeState(value: unknown): AgentState | undefined {
  if (typeof value === "string" && STATE_NAMES.has(value)) return value as AgentState;
  return undefined;
}

export function parsePlannerEvent(raw: unknown): PlannerStreamEvent | null {
  const data = typeof raw === "string" ? safeJsonParse(raw) : raw;
  if (!isRecord(data)) return null;

  return {
    event: normalizeEventName(data.event, data.type),
    type: typeof data.type === "string" ? data.type : undefined,
    state: normalizeState(data.state),
    step: typeof data.step === "number" ? data.step : undefined,
    message: typeof data.message === "string" ? data.message : undefined,
    session_id: typeof data.session_id === "string" ? data.session_id : undefined,
    payload: isRecord(data.payload) ? data.payload : undefined,
    created_at: typeof data.created_at === "string" ? data.created_at : undefined
  };
}

function safeJsonParse(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

export function isTerminalPlannerState(state: AgentState | undefined) {
  return ["completed", "failed", "cancelled", "COMPLETED", "FAILED", "CANCELLED"].includes(
    state ?? ""
  );
}

export function formatPlannerEvent(event: PlannerStreamEvent) {
  const state = event.state ? `[${String(event.state).toUpperCase()}] ` : "";
  const step = typeof event.step === "number" ? `Step ${event.step}: ` : "";
  return `${state}${step}${event.message ?? event.event}`;
}
