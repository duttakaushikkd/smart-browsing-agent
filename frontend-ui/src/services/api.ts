import type { ApiError, QueryRequest, QueryResponse, StreamChunk } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    if (contentType.includes("application/json")) {
      const data = (await response.json()) as Partial<ApiError>;
      message = data.message || message;
    } else {
      const text = await response.text();
      if (text.trim()) message = text;
    }
    throw new Error(message);
  }

  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  throw new Error("Unexpected API response format.");
}

export async function submitQuery(payload: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse<QueryResponse>(response);
}

export async function submitQueryStream(
  payload: QueryRequest,
  onChunk?: (chunk: StreamChunk) => void
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream, application/json"
    },
    body: JSON.stringify(payload)
  });

  const contentType = response.headers.get("content-type") ?? "";

  if (!response.ok) {
    await parseResponse<QueryResponse>(response);
  }

  if (!response.body || !contentType.includes("text/event-stream")) {
    return parseResponse<QueryResponse>(response);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let accumulated = "";
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const segments = buffer.split("\n\n");
    buffer = segments.pop() ?? "";

    for (const segment of segments) {
      const lines = segment
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const data = line.replace(/^data:\s*/, "");
        if (!data || data === "[DONE]") continue;

        try {
          const chunk = JSON.parse(data) as StreamChunk;
          accumulated += chunk.text ?? "";
          onChunk?.(chunk);
        } catch {
          accumulated += data;
          onChunk?.({ text: data });
        }
      }
    }
  }

  return { response: accumulated };
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}
