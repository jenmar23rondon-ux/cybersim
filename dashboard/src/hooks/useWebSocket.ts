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
  const [scope, setScope] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setScope(correlationId);
    setConnected(false);
    if (!correlationId) {
      setEvents([]);
      setConnected(false);
      wsRef.current?.close();
      return;
    }
    setEvents([]);
    let closedByUs = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      if (closedByUs) return;
      const ws = new WebSocket(`${WS_URL}/ws/${correlationId}`);
      wsRef.current = ws;
      ws.onopen = () => { if (!closedByUs) setConnected(true); };
      ws.onclose = () => {
        if (closedByUs) return;
        setConnected(false);
        reconnectTimer = setTimeout(connect, 1000);
      };
      ws.onmessage = (msg) => {
        if (closedByUs) return;
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
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [correlationId]);

  return { events: scope === correlationId ? events : [], connected: scope === correlationId && connected };
}
