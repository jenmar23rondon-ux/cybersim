import { useEffect, useState } from "react";
import { api } from "../api";
import type { TargetProfile, TargetProbe } from "../types";

interface Props {
  onApply: (target: { host: string; port: number }) => void;
}

const STORAGE_KEY = "cybersim.targetProfiles";
const LOCAL_PORT_TARGETS: Record<number, string> = {
  3001: "vuln-node-api",
  3002: "juice-shop",
  3003: "mini-vuln-app",
  4280: "dvwa",
  2222: "weak-ssh",
};

export function TargetConnector({ onApply }: Props) {
  const [name, setName] = useState("CyberBank local app");
  const [url, setUrl] = useState("http://mini-vuln-app:3003");
  const [healthPath, setHealthPath] = useState("/health");
  const [profiles, setProfiles] = useState<TargetProfile[]>([]);
  const [probe, setProbe] = useState<TargetProbe | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setProfiles(JSON.parse(raw));
    } catch {
      setProfiles([]);
    }
  }, []);

  const saveProfiles = (next: TargetProfile[]) => {
    setProfiles(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  };

  const testConnection = async () => {
    setChecking(true);
    setError(null);
    setProbe(null);
    try {
      const result = await api.probeTarget(url, healthPath);
      setProbe(result);
      if (!result.ok) {
        setError(result.error || `Probe returned HTTP ${result.status_code || "unknown"}`);
      }
      return result;
    } catch (err: any) {
      setError(err.message || String(err));
      return null;
    } finally {
      setChecking(false);
    }
  };

  const saveProfile = async () => {
    const result = probe?.ok ? probe : await testConnection();
    if (!result?.ok) return;
    const profile: TargetProfile = {
      name: name.trim() || result.attack_host,
      url,
      host: result.attack_host,
      port: result.port,
      scheme: result.scheme,
      healthPath,
      lastStatus: "connected",
      lastChecked: new Date().toISOString(),
    };
    const next = [profile, ...profiles.filter((item) => item.host !== profile.host || item.port !== profile.port)].slice(0, 6);
    saveProfiles(next);
    onApply({ host: profile.host, port: profile.port });
  };

  const removeProfile = (profile: TargetProfile) => {
    saveProfiles(profiles.filter((item) => item !== profile));
  };

  const applyProfile = (profile: TargetProfile) => {
    onApply({
      host: normalizeLaunchHost(profile.host, profile.port),
      port: profile.port,
    });
  };

  return (
    <div className="panel connector">
      <div className="section-title">
        <h2>Target Connector</h2>
        <div className="spacer" />
        <span className="connector-guard">Local / allowlisted only</span>
      </div>

      <p className="muted">
        Connect another authorized app, verify it is reachable from the lab, then apply it to the selected attack.
      </p>

      <div className="connector-form">
        <div>
          <label>Profile name</label>
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </div>
        <div>
          <label>App URL or Docker host</label>
          <input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="http://mini-vuln-app:3003" />
        </div>
        <div>
          <label>Health path</label>
          <input value={healthPath} onChange={(event) => setHealthPath(event.target.value)} />
        </div>
      </div>

      <div className="connector-actions">
        <button className="btn ghost compact" type="button" disabled={checking || !url} onClick={testConnection}>
          {checking ? "Checking..." : "Test connection"}
        </button>
        <button className="btn compact" type="button" disabled={checking || !url} onClick={saveProfile}>
          Save & apply
        </button>
      </div>

      {probe && (
        <div className={`connector-result ${probe.ok ? "ok" : "fail"}`}>
          <strong>{probe.ok ? "Connected" : "Connection failed"}</strong>
          <span>
            {probe.host}:{probe.port} {"->"} {probe.status_code || probe.error || "no response"}
          </span>
          {probe.attack_host !== probe.host && (
            <span>Docker target: {probe.attack_host}:{probe.port}</span>
          )}
        </div>
      )}
      {error && <div className="connector-error">{error}</div>}

      {profiles.length > 0 && (
        <div className="profile-list">
          {profiles.map((profile) => (
            <div className="profile-card" key={`${profile.host}:${profile.port}`}>
              <div>
                <strong>{profile.name}</strong>
                <span>{profile.host}:{profile.port}</span>
              </div>
              <button type="button" onClick={() => applyProfile(profile)}>Apply</button>
              <button type="button" onClick={() => removeProfile(profile)}>Remove</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function normalizeLaunchHost(host: string, port: number) {
  if (host === "localhost" || host === "127.0.0.1") {
    return LOCAL_PORT_TARGETS[port] || "host.docker.internal";
  }
  return host;
}
