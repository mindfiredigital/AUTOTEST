export type WSMessageType =
  | "PING"
  | "PONG"
  | "AUTH"
  | "ERROR"
  | "EVENT"
  | "SUBSCRIBE"
  | "UNSUBSCRIBE";

export interface WSBaseMessage<T = unknown> {
  type: WSMessageType;
  payload: T;
  timestamp?: number;
}

/* Example payloads */
export interface AuthPayload {
  token: string;
}

export interface EventPayload {
  event: string;
  data: unknown;
}

export interface ErrorPayload {
  message: string;
  code?: number;
}
