import type { PlannerConnectionState, PlannerStreamEvent } from "@/types";
import { parsePlannerEvent } from "./plannerEvents";

type PlannerSocketOptions = {
  streamUrl: string;
  onEvent: (event: PlannerStreamEvent) => void;
  onConnectionChange?: (state: PlannerConnectionState) => void;
  onError?: (message: string) => void;
  heartbeatTimeoutMs?: number;
  maxReconnectAttempts?: number;
};

const BASE_BACKOFF_MS = 500;
const MAX_BACKOFF_MS = 8000;

export class PlannerStreamClient {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private closedByClient = false;
  private heartbeatTimer: number | null = null;
  private reconnectTimer: number | null = null;

  constructor(private readonly options: PlannerSocketOptions) {}

  connect() {
    this.closedByClient = false;
    this.openSocket("connecting");
  }

  disconnect() {
    this.closedByClient = true;
    this.clearTimers();
    this.socket?.close(1000, "client_disconnect");
    this.socket = null;
    this.options.onConnectionChange?.("disconnected");
  }

  private openSocket(state: PlannerConnectionState) {
    if (typeof window === "undefined") return;

    this.options.onConnectionChange?.(state);
    this.socket?.close();
    this.socket = new WebSocket(this.options.streamUrl);

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.options.onConnectionChange?.("connected");
      this.resetHeartbeatTimer();
    };

    this.socket.onmessage = (message) => {
      this.resetHeartbeatTimer();
      const parsed = parsePlannerEvent(message.data);
      if (!parsed) {
        this.options.onError?.("Received malformed planner event.");
        return;
      }
      this.options.onEvent(parsed);
    };

    this.socket.onerror = () => {
      this.options.onError?.("Planner stream connection error.");
    };

    this.socket.onclose = () => {
      this.clearHeartbeatTimer();
      if (!this.closedByClient) this.scheduleReconnect();
    };
  }

  private resetHeartbeatTimer() {
    this.clearHeartbeatTimer();
    const timeout = this.options.heartbeatTimeoutMs ?? 45_000;
    this.heartbeatTimer = window.setTimeout(() => {
      this.options.onConnectionChange?.("stale");
      this.socket?.close();
    }, timeout);
  }

  private scheduleReconnect() {
    if (this.closedByClient) return;

    const maxAttempts = this.options.maxReconnectAttempts ?? 8;
    if (this.reconnectAttempts >= maxAttempts) {
      this.options.onConnectionChange?.("disconnected");
      this.options.onError?.("Planner stream disconnected. Refresh status to resume.");
      return;
    }

    this.options.onConnectionChange?.("reconnecting");
    const delay = Math.min(BASE_BACKOFF_MS * 2 ** this.reconnectAttempts, MAX_BACKOFF_MS);
    this.reconnectAttempts += 1;
    this.reconnectTimer = window.setTimeout(() => this.openSocket("reconnecting"), delay);
  }

  private clearHeartbeatTimer() {
    if (!this.heartbeatTimer) return;
    window.clearTimeout(this.heartbeatTimer);
    this.heartbeatTimer = null;
  }

  private clearTimers() {
    this.clearHeartbeatTimer();
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}
