import type {
  AgentCancelResponse,
  AgentContinueRequest,
  AgentStartRequest,
  AgentStartResponse,
  AgentStatusResponse,
  ApiError
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function getMessageFromErrorBody(data: unknown, fallback: string) {
  if (!data || typeof data !== "object") return fallback;
  const record = data as Record<string, unknown>;
  if (typeof record.message === "string") return record.message;
  if (typeof record.detail === "string") return record.detail;
  if (record.error && typeof record.error === "object") {
    const error = record.error as Partial<ApiError>;
    if (typeof error.message === "string") return error.message;
  }
  return fallback;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";

  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`;
    if (contentType.includes("application/json")) {
      throw new Error(getMessageFromErrorBody(await response.json(), fallback));
    }

    const text = await response.text();
    throw new Error(text.trim() || fallback);
  }

  if (!contentType.includes("application/json")) {
    throw new Error("Unexpected planner response format.");
  }

  return (await response.json()) as T;
}

export class PlannerApiClient {
  constructor(private readonly baseUrl = API_BASE_URL) {}

  getBaseUrl() {
    return this.baseUrl;
  }

  getStreamUrl(sessionId: string) {
    const url = new URL(this.baseUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `/agent/${encodeURIComponent(sessionId)}/stream`;
    url.search = "";
    return url.toString();
  }

  async start(payload: AgentStartRequest): Promise<AgentStartResponse> {
    const response = await fetch(`${this.baseUrl}/agent/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return parseJsonResponse<AgentStartResponse>(response);
  }

  async continue(sessionId: string, payload: AgentContinueRequest): Promise<AgentStatusResponse> {
    const response = await fetch(`${this.baseUrl}/agent/${encodeURIComponent(sessionId)}/continue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return parseJsonResponse<AgentStatusResponse>(response);
  }

  async status(sessionId: string): Promise<AgentStatusResponse> {
    const response = await fetch(`${this.baseUrl}/agent/${encodeURIComponent(sessionId)}/status`);
    return parseJsonResponse<AgentStatusResponse>(response);
  }

  async cancel(sessionId: string): Promise<AgentCancelResponse> {
    const response = await fetch(`${this.baseUrl}/agent/${encodeURIComponent(sessionId)}/cancel`, {
      method: "POST"
    });
    return parseJsonResponse<AgentCancelResponse>(response);
  }
}

export const plannerApi = new PlannerApiClient();

export function getPlannerApiBaseUrl() {
  return API_BASE_URL;
}
