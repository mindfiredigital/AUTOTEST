import React, { createContext, useContext, useMemo, useCallback, useRef, useEffect } from "react";
import useWebSocket, { ReadyState, type Options } from "react-use-websocket";

import { WS_CONFIG } from "@/config/websocket";
import type { WSBaseMessage, WSMessageType } from "@/types/websocket";

// const WS_URL = "ws://localhost:8000/api/v1/ws";
const WS_URL = import.meta.env.VITE_WS_URL;

type WSContextType = {
  sendMessage: <T>(type: WSMessageType, payload: T) => void;
  lastMessage: WSBaseMessage | null;
  connectionState: ReadyState;
  isConnected: boolean;
};

const WSContext = createContext<WSContextType | null>(null);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const lastJsonMessageRef = useRef<WSBaseMessage | null>(null);
  const heartbeatIntervalRef = useRef<number | null>(null);

  const socketOptions: Options = useMemo(() => ({
    shouldReconnect: () => true,
    reconnectAttempts: WS_CONFIG.reconnectAttempts,
    reconnectInterval: WS_CONFIG.reconnectInterval,

    onOpen: () => {
      console.info("WebSocket connected");
      
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = setInterval(() => {
        if (wsReadyStateRef.current === ReadyState.OPEN) {
          sendJsonMessage({ type: "PING", payload: {}, timestamp: Date.now() });
        }
      }, WS_CONFIG.heartbeatInterval);
    },

    onClose: (event) => {
      console.warn("WebSocket disconnected", event);
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
    },

    onError: (event) => console.error("WebSocket error:", event),

    filter: () => true,
  }), []);

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(WS_URL, socketOptions);

  const wsReadyStateRef = useRef(readyState);
  useEffect(() => { wsReadyStateRef.current = readyState; }, [readyState]);

  useEffect(() => { lastJsonMessageRef.current = lastJsonMessage as WSBaseMessage | null; }, [lastJsonMessage]);

  const sendMessage = useCallback(<T,>(type: WSMessageType, payload: T) => {
    const message: WSBaseMessage<T> = { type, payload, timestamp: Date.now() };
    sendJsonMessage(message);
  }, [sendJsonMessage]);

  const value: WSContextType = {
    sendMessage,
    lastMessage: lastJsonMessageRef.current,
    connectionState: readyState,
    isConnected: readyState === ReadyState.OPEN,
  };

  return <WSContext.Provider value={value}>{children}</WSContext.Provider>;
};

export const useWebSocketContext = (): WSContextType => {
  const ctx = useContext(WSContext);
  if (!ctx) throw new Error("useWebSocketContext must be used inside WebSocketProvider");
  return ctx;
};
