export type QueryRequest = {
  query: string;
};

export type QueryResponse = {
  response: string;
};

export type ResponseStatus = "idle" | "loading" | "success" | "error";

export type ConversationEntry = {
  id: string;
  query: string;
  response: string;
  createdAt: string;
};

export type ApiError = {
  message: string;
  status?: number;
};

export type StreamChunk = {
  text: string;
  done?: boolean;
};
