export type ResponseStatus = "idle" | "loading" | "success" | "error";

export type AgentState =
  | "idle"
  | "planning"
  | "executing"
  | "observing"
  | "replanning"
  | "waiting_user"
  | "completed"
  | "failed"
  | "cancelled"
  | "IDLE"
  | "PLANNING"
  | "EXECUTING"
  | "OBSERVING"
  | "REPLANNING"
  | "WAITING_USER"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type PlannerEventName =
  | "planner_update"
  | "tool_execution"
  | "observation"
  | "screenshot"
  | "recovery"
  | "error"
  | "completion"
  | "heartbeat";

export type PlannerStreamEvent = {
  event: PlannerEventName;
  state?: AgentState;
  step?: number;
  message?: string;
  session_id?: string;
  type?: string;
  payload?: Record<string, unknown>;
  created_at?: string;
};

export type PlannerTimelineEvent = {
  state: AgentState;
  message: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
};

export type AgentStartRequest = {
  goal: string;
  metadata?: Record<string, unknown>;
};

export type AgentStartResponse = {
  session_id: string;
  state: AgentState;
};

export type AgentContinueRequest = {
  user_input?: string | null;
};

export type AgentStatusResponse = {
  session_id: string;
  goal: string;
  state: AgentState;
  current_step: number;
  plan_summary: string | null;
  final_result: string | null;
  error: string | null;
  timeline: PlannerTimelineEvent[];
  metadata?: Record<string, unknown>;
};

export type AgentCancelResponse = {
  session_id: string;
  state: AgentState;
};

export type PlannerConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "stale";

export type ConversationEntry = {
  id: string;
  sessionId?: string;
  query: string;
  response: string;
  plannerState?: AgentState;
  currentStep?: number;
  events?: PlannerStreamEvent[];
  createdAt: string;
};

export type ApiError = {
  message: string;
  status?: number;
};
