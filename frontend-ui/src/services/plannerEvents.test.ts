import { describe, expect, it } from "vitest";
import { formatPlannerEvent, isTerminalPlannerState, parsePlannerEvent } from "./plannerEvents";

describe("planner event parser", () => {
  it("parses planner_update events from the stream", () => {
    const event = parsePlannerEvent(
      JSON.stringify({
        event: "planner_update",
        state: "EXECUTING",
        step: 3,
        message: "Opening amazon.in",
        session_id: "abc"
      })
    );

    expect(event).toEqual({
      event: "planner_update",
      type: undefined,
      state: "EXECUTING",
      step: 3,
      message: "Opening amazon.in",
      session_id: "abc",
      payload: undefined,
      created_at: undefined
    });
  });

  it("normalizes planner service tool_result events to frontend tool_execution events", () => {
    const event = parsePlannerEvent({
      type: "tool_result",
      state: "OBSERVING",
      step: 2,
      message: "Tool execution finished"
    });

    expect(event?.event).toBe("tool_execution");
  });

  it("rejects malformed stream messages", () => {
    expect(parsePlannerEvent("not-json")).toBeNull();
    expect(parsePlannerEvent(null)).toBeNull();
  });

  it("formats events without exposing planner internals", () => {
    const event = parsePlannerEvent({
      event: "planner_update",
      state: "PLANNING",
      step: 1,
      message: "Planning next action"
    });

    expect(event ? formatPlannerEvent(event) : "").toBe(
      "[PLANNING] Step 1: Planning next action"
    );
  });

  it("detects terminal planner states", () => {
    expect(isTerminalPlannerState("COMPLETED")).toBe(true);
    expect(isTerminalPlannerState("executing")).toBe(false);
  });
});
