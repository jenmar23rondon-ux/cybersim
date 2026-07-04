import type { Campaign } from "../types";

const ICON: Record<string, string> = {
  pending: "O",
  running: "...",
  success: "OK",
  failed: "X",
};

export function CampaignProgress({ campaign }: { campaign: Campaign | null }) {
  if (!campaign) {
    return <p className="muted">Launch a scenario to see step-by-step progress here.</p>;
  }
  return (
    <div>
      <div className="section-title">
        <strong>{campaign.name}</strong>
        <div className="spacer" />
        <span className={`pill ${campaign.status}`}>{campaign.status}</span>
      </div>
      <ol className="campaign-steps">
        {campaign.steps.map((s, i) => (
          <li key={i} className={`cstep ${s.status}`}>
            <span className="cicon">{ICON[s.status] || "O"}</span>
            <div>
              <div className="ctitle">
                {s.attack_type} to {s.target}
              </div>
              <div className="cnarr">{s.narrative}</div>
            </div>
            <div className="spacer" />
            <span className={`pill ${s.status === "pending" ? "running" : s.status}`}>
              {s.status}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
