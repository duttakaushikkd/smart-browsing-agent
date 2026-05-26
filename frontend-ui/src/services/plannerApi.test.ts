import { afterEach, describe, expect, it, vi } from "vitest";
import { PlannerApiClient } from "./plannerApi";

describe("PlannerApiClient", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts planner sessions through /agent/start", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ session_id: "abc", state: "planning" }), {
        status: 202,
        headers: { "content-type": "application/json" }
      })
    );
    const client = new PlannerApiClient("http://planner.test");

    const response = await client.start({ goal: "Open example.com" });

    expect(response.session_id).toBe("abc");
    expect(fetchMock).toHaveBeenCalledWith("http://planner.test/agent/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: "Open example.com" })
    });
  });

  it("builds WebSocket stream URLs from HTTP base URLs", () => {
    const client = new PlannerApiClient("https://planner.test/base");

    expect(client.getStreamUrl("abc 123")).toBe("wss://planner.test/agent/abc%20123/stream");
  });

  it("surfaces planner API errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Session not found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      })
    );
    const client = new PlannerApiClient("http://planner.test");

    await expect(client.status("missing")).rejects.toThrow("Session not found");
  });
});
