import type { AttackModule, AttackRun, Campaign, DefensePlaybook, LabBoundary, Metrics, RemediationGuide, Scenario, TargetProbe } from "./types";

export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
export const WS_URL = (import.meta.env.VITE_WS_URL || API_URL.replace(/^http/, "ws")).replace(/\/$/, "");

function sessionQuery(boundary: LabBoundary | null) {
  return boundary ? `?${new URLSearchParams({
    after_run_id: String(boundary.after_run_id),
    after_campaign_id: String(boundary.after_campaign_id),
  })}` : "";
}

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

async function request<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  try {
    const res = await fetch(input, init);
    return j<T>(res);
  } catch (err: any) {
    if (err instanceof TypeError) {
      throw new Error(
        `No se pudo conectar con el backend (${API_URL}). Revisa que VITE_API_URL apunte al servicio backend publico y que ese backend este online.`
      );
    }
    throw err;
  }
}

export const api = {
  modules: () => request<AttackModule[]>(`${API_URL}/api/modules`),

  metrics: (boundary: LabBoundary | null = null) => request<Metrics>(`${API_URL}/api/metrics${sessionQuery(boundary)}`),

  labBaseline: () => request<LabBoundary>(`${API_URL}/api/lab/baseline`),

  playbooks: () => request<DefensePlaybook[]>(`${API_URL}/api/defense/playbooks`),

  remediationGuides: () =>
    request<RemediationGuide[]>(`${API_URL}/api/remediation/guides`),

  probeTarget: (url: string, path: string) =>
    request<TargetProbe>(`${API_URL}/api/targets/probe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, path }),
    }),

  launch: (attack_type: string, target: string, params: Record<string, any>) =>
    request<{ correlation_id: string; status: string }>(`${API_URL}/api/attacks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attack_type, target, params }),
    }),

  history: (boundary: LabBoundary | null = null) => request<AttackRun[]>(`${API_URL}/api/attacks${sessionQuery(boundary)}`),

  run: (id: string) => request<AttackRun>(`${API_URL}/api/attacks/${id}`),

  reportUrl: (id: string) => `${API_URL}/api/attacks/${id}/report`,

  // --- Guided scenarios / auto-campaigns ---
  scenarios: () => request<Scenario[]>(`${API_URL}/api/scenarios`),

  launchCampaign: (scenario_id: string) =>
    request<{ campaign_id: string; status: string }>(`${API_URL}/api/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id }),
    }),

  campaign: (id: string) =>
    request<Campaign>(`${API_URL}/api/campaigns/${id}`),

  campaignReportUrl: (id: string) => `${API_URL}/api/campaigns/${id}/report`,
};
