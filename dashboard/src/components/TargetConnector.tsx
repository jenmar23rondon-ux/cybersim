import { useEffect, useState } from "react";
import { API_URL, api } from "../api";
import type { TargetProfile, TargetProbe } from "../types";

interface Props {
  onApply: (target: { host: string; port: number; scheme?: string }) => void;
}

const STORAGE_KEY = "cybersim.targetProfiles";
const CLOUD_TARGET_URL = import.meta.env.VITE_CLOUD_TARGET_URL || "";
const API_IS_LOCAL = API_URL.includes("localhost") || API_URL.includes("127.0.0.1");
const LOCAL_DOCKER_HOSTS = new Set(["mini-vuln-app", "vuln-node-api", "juice-shop", "dvwa", "weak-ssh"]);
const CLOUD_TARGET_IS_DOCKER_HOST = isDockerOnlyUrl(CLOUD_TARGET_URL);
const DEFAULT_TARGET_URL = CLOUD_TARGET_IS_DOCKER_HOST ? "" : CLOUD_TARGET_URL || (API_IS_LOCAL ? "http://mini-vuln-app:3003" : "");
const TARGET_PLACEHOLDER = API_IS_LOCAL ? "http://mini-vuln-app:3003" : "https://your-target.up.railway.app";
const LOCAL_PORT_TARGETS: Record<number, string> = {
  3001: "vuln-node-api",
  3002: "juice-shop",
  3003: "mini-vuln-app",
  4280: "dvwa",
  2222: "weak-ssh",
};

export function TargetConnector({ onApply }: Props) {
  const [name, setName] = useState(API_IS_LOCAL ? "CyberBank local app" : "CyberBank cloud Docker");
  const [url, setUrl] = useState(DEFAULT_TARGET_URL);
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

  const cloudDockerHostError = () => {
    if (!url.trim()) {
      return "Pega la URL publica real de Railway del CyberBank target. No puede quedar vacio.";
    }
    if (isPlaceholderUrl(url)) {
      return "Esa es solo una URL de ejemplo. Reemplazala por la URL real de Railway de tu CyberBank target.";
    }
    if (!API_IS_LOCAL && isDockerOnlyUrl(url)) {
      return "Estas en modo cloud: pega la URL publica de Railway del Docker CyberBank, no el hostname interno mini-vuln-app.";
    }
    return null;
  };

  const updateUrl = (nextUrl: string) => {
    setUrl(nextUrl);
    setProbe(null);
    setError(null);
  };

  const testConnection = async () => {
    const validationError = cloudDockerHostError();
    if (validationError) {
      setProbe(null);
      setError(validationError);
      return null;
    }
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
    onApply({ host: profile.host, port: profile.port, scheme: profile.scheme });
  };

  const removeProfile = (profile: TargetProfile) => {
    saveProfiles(profiles.filter((item) => item !== profile));
  };

  const applyProfile = (profile: TargetProfile) => {
    onApply({
      host: normalizeLaunchHost(profile.host, profile.port),
      port: profile.port,
      scheme: profile.scheme,
    });
  };

  return (
    <div className="panel connector">
      <div className="section-title">
        <h2>Target Connector</h2>
        <div className="spacer" />
        <span className="connector-guard">Lab / allowlisted only</span>
      </div>

      <p className="muted">
        {API_IS_LOCAL
          ? "Connect your local Docker target, verify it is reachable, then apply it to the selected attack."
          : "Paste the public Railway URL for your CyberBank Docker, verify it is reachable, then apply it to the selected attack."}
      </p>
      {!API_IS_LOCAL && (!CLOUD_TARGET_URL || CLOUD_TARGET_IS_DOCKER_HOST) && (
        <div className="connector-hint">
          Cloud mode cannot resolve Docker hostnames like mini-vuln-app. Use the public target URL from Railway Networking.
          {CLOUD_TARGET_IS_DOCKER_HOST && " Your VITE_CLOUD_TARGET_URL is currently pointing to a local Docker hostname."}
        </div>
      )}

      <div className="connector-form">
        <div>
          <label>Profile name</label>
          <input value={name} onChange={(event) => setName(event.target.value)} />
        </div>
        <div>
          <label>App URL or Docker host</label>
          <input value={url} onChange={(event) => updateUrl(event.target.value)} placeholder={TARGET_PLACEHOLDER} />
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

function isDockerOnlyUrl(value: string) {
  if (!value) return false;
  try {
    const parsed = new URL(value.includes("://") ? value : `http://${value}`);
    return LOCAL_DOCKER_HOSTS.has(parsed.hostname);
  } catch {
    return LOCAL_DOCKER_HOSTS.has(value.split(":")[0]);
  }
}

function isPlaceholderUrl(value: string) {
  const normalized = value.trim().toLowerCase();
  return normalized.includes("your-target") || normalized.includes("your-cyberbank-target");
}
