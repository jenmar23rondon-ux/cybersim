import { useEffect, useRef, useState } from "react";
import type { LogEvent } from "../types";
import { WS_URL } from "../api";

/**
 * Subscribes to a single attack run's live log stream. When `correlationId`
 * changes, it reconnects to the new run's socket. Auto-reconnects on drop while
 * a run is active.
 */
export function useAttackSocket(correlationId: string | null) {
  const [events, setEvents] = useState<LogEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!correlationId) return;
    setEvents([]);
    let closedByUs = false;

    const connect = () => {
      const ws = new WebSocket(`${WS_URL}/ws/${correlationId}`);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closedByUs) setTimeout(connect, 1000);
      };
      ws.onmessage = (msg) => {
        try {
          const ev = JSON.parse(msg.data) as LogEvent;
          setEvents((prev) => [...prev, ev]);
        } catch {
          /* ignore malformed */
        }
      };
    };
    connect();

    return () => {
      closedByUs = true;
      wsRef.current?.close();
    };
  }, [correlationId]);

  return { events, connected };
}
