import type { AttackModule, AttackRun, Campaign, DefensePlaybook, Metrics, RemediationGuide, Scenario } from "./types";

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  modules: () => fetch(`${API_URL}/api/modules`).then((r) => j<AttackModule[]>(r)),

  metrics: () => fetch(`${API_URL}/api/metrics`).then((r) => j<Metrics>(r)),

  playbooks: () => fetch(`${API_URL}/api/defense/playbooks`).then((r) => j<DefensePlaybook[]>(r)),

  remediationGuides: () =>
    fetch(`${API_URL}/api/remediation/guides`).then((r) => j<RemediationGuide[]>(r)),

  launch: (attack_type: string, target: string, params: Record<string, any>) =>
    fetch(`${API_URL}/api/attacks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attack_type, target, params }),
    }).then((r) => j<{ correlation_id: string; status: string }>(r)),

  history: () => fetch(`${API_URL}/api/attacks`).then((r) => j<AttackRun[]>(r)),

  run: (id: string) => fetch(`${API_URL}/api/attacks/${id}`).then((r) => j<AttackRun>(r)),

  reportUrl: (id: string) => `${API_URL}/api/attacks/${id}/report`,

  // --- Guided scenarios / auto-campaigns ---
  scenarios: () => fetch(`${API_URL}/api/scenarios`).then((r) => j<Scenario[]>(r)),

  launchCampaign: (scenario_id: string) =>
    fetch(`${API_URL}/api/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id }),
    }).then((r) => j<{ campaign_id: string; status: string }>(r)),

  campaign: (id: string) =>
    fetch(`${API_URL}/api/campaigns/${id}`).then((r) => j<Campaign>(r)),

  campaignReportUrl: (id: string) => `${API_URL}/api/campaigns/${id}/report`,
};
