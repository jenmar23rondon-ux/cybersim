import { useEffect, useRef } from "react";
import type { LogEvent } from "../types";

export function LiveLogs({ events }: { events: LogEvent[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest line.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="terminal">
      {events.length === 0 && (
        <div className="logline info">
          <span className="msg">Waiting for attack events…</span>
        </div>
      )}
      {events.map((e, i) => (
        <div key={i} className={`logline ${e.level}`}>
          <span className="ts">{new Date(e.timestamp).toLocaleTimeString()}</span>
          <span className="lvl">{e.level}</span>
          <span className="msg">{e.message}</span>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
