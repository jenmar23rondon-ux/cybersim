export interface AttackModule {
  id: string;
  name: string;
  description: string;
  default_target: string;
  mitre: string;
  params_schema: Record<string, any>;
}

export interface LogEvent {
  correlation_id: string;
  attack_type: string;
  level: "info" | "success" | "warn" | "error";
  message: string;
  progress: number;
  data: Record<string, any>;
  timestamp: string;
}

export interface AIExplanation {
  title?: string;
  what_it_does?: string;
  vulnerability_exploited?: string;
  remediation?: string[];
  mitre?: { id?: string; name?: string };
  generated_by?: string;
  note?: string;
}

export interface DefensePlaybook {
  attack_type: string;
  severity: "low" | "medium" | "high" | "critical";
  business_impact: string;
  detections: string[];
  securewatch_query: string;
  triage: string[];
  remediation: string[];
  risk_score: number;
}

export interface DefenseSummary extends DefensePlaybook {
  confirmed: boolean;
  log_level_counts: Record<string, number>;
  event_count: number;
}

export interface RemediationGuide {
  attack_type: string;
  title: string;
  goal: string;
  applies_to: string[];
  difficulty: "easy" | "medium" | "hard" | string;
  steps: string[];
  secure_pattern: string;
  verify: string[];
}

export interface ScenarioStep {
  attack_type: string;
  target: string;
  narrative: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  steps: ScenarioStep[];
}

export interface CampaignStep {
  attack_type: string;
  target: string;
  narrative: string;
  correlation_id: string | null;
  status: "pending" | "running" | "success" | "failed";
}

export interface Campaign {
  id: number;
  campaign_id: string;
  scenario_id: string;
  name: string;
  status: "running" | "success" | "failed";
  steps: CampaignStep[];
  summary: Record<string, any>;
  started_at: string | null;
  finished_at: string | null;
}

export interface AttackRun {
  id: number;
  correlation_id: string;
  attack_type: string;
  target: string;
  status: "running" | "success" | "failed";
  params: Record<string, any>;
  logs: LogEvent[];
  result: Record<string, any>;
  ai_explanation: AIExplanation | null;
  defense?: DefenseSummary;
  started_at: string | null;
  finished_at: string | null;
}

export interface Metrics {
  generated_at: string;
  total_runs: number;
  confirmed_findings: number;
  campaigns: number;
  status_counts: Record<string, number>;
  attack_counts: Record<string, number>;
  average_risk_score: number;
  top_findings: Array<{
    correlation_id: string;
    attack_type: string;
    target: string;
    status: string;
    risk_score: number;
    started_at: string | null;
  }>;
}

export interface TargetProbe {
  ok: boolean;
  host: string;
  port: number;
  scheme: string;
  probe_url: string;
  status_code?: number;
  content_type?: string;
  error?: string;
  details: {
    host: string;
    explicitly_allowlisted: boolean;
    resolved_ip: string | null;
    private_or_loopback: boolean;
    allowed: boolean;
  };
}

export interface TargetProfile {
  name: string;
  url: string;
  host: string;
  port: number;
  scheme: string;
  healthPath: string;
  lastStatus: "connected" | "failed";
  lastChecked: string;
}
