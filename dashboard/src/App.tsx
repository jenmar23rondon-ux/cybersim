import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type {
  AIExplanation,
  AttackModule,
  AttackRun,
  Campaign,
  DefensePlaybook,
  DefenseSummary,
  Metrics,
  RemediationGuide,
  Scenario,
} from "./types";
import { useAttackSocket } from "./hooks/useWebSocket";
import { AttackSelector } from "./components/AttackSelector";
import { LaunchPanel } from "./components/LaunchPanel";
import { LiveLogs } from "./components/LiveLogs";
import { ProgressBar } from "./components/ProgressBar";
import { StatusIndicator } from "./components/StatusIndicator";
import { AIExplainer } from "./components/AIExplainer";
import { HistoryPanel } from "./components/HistoryPanel";
import { ScenarioPanel } from "./components/ScenarioPanel";
import { CampaignProgress } from "./components/CampaignProgress";
import { MetricsStrip } from "./components/MetricsStrip";
import { DefensePanel } from "./components/DefensePanel";
import { TargetShowcase } from "./components/TargetShowcase";
import { RemediationLab } from "./components/RemediationLab";
import { PWAInstall } from "./components/PWAInstall";
import { ImpactMap } from "./components/ImpactMap";

type Status = "running" | "success" | "failed";
type Mode = "single" | "scenario";

export default function App() {
  const [mode, setMode] = useState<Mode>("single");
  const [modules, setModules] = useState<AttackModule[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [launching, setLaunching] = useState(false);
  const [correlationId, setCorrelationId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [explanation, setExplanation] = useState<AIExplanation | null>(null);
  const [history, setHistory] = useState<AttackRun[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [playbooks, setPlaybooks] = useState<DefensePlaybook[]>([]);
  const [remediationGuides, setRemediationGuides] = useState<RemediationGuide[]>([]);
  const [activeDefense, setActiveDefense] = useState<DefenseSummary | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [isCampaign, setIsCampaign] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { events, connected } = useAttackSocket(correlationId);

  const selected = useMemo(
    () => modules.find((m) => m.id === selectedId) || null,
    [modules, selectedId]
  );
  const selectedPlaybook = useMemo(
    () => playbooks.find((p) => p.attack_type === selectedId) || null,
    [playbooks, selectedId]
  );
  const defenseView = activeDefense || selectedPlaybook;
  const remediationView = useMemo(
    () => remediationGuides.find((g) => g.attack_type === selectedId) || null,
    [remediationGuides, selectedId]
  );
  const progress = events.length ? events[events.length - 1].progress : 0;

  useEffect(() => {
    api.modules().then((m) => {
      setModules(m);
      if (m.length) setSelectedId(m[0].id);
    }).catch((e) => setError(String(e)));
    api.scenarios().then((s) => {
      setScenarios(s);
      if (s.length) setSelectedScenario(s[0].id);
    }).catch(() => {});
    api.playbooks().then(setPlaybooks).catch(() => {});
    api.remediationGuides().then(setRemediationGuides).catch(() => {});
    refreshMetrics();
    refreshHistory();
  }, []);

  useEffect(() => {
    const final = events.find((e) => e.data?.final);
    if (!final) return;
    setStatus(final.data.status as Status);
    setLaunching(false);
    refreshHistory();
    refreshMetrics();
    if (isCampaign && correlationId) {
      api.campaign(correlationId).then(setCampaign).catch(() => {});
    } else {
      setExplanation((final.data.explanation as AIExplanation) || null);
      if (correlationId) {
        api.run(correlationId).then((run) => setActiveDefense(run.defense || null)).catch(() => {});
      }
    }
  }, [events, isCampaign, correlationId]);

  useEffect(() => {
    if (isCampaign && correlationId && events.length) {
      api.campaign(correlationId).then(setCampaign).catch(() => {});
    }
  }, [events.length, isCampaign, correlationId]);

  const refreshHistory = () => api.history().then(setHistory).catch(() => {});
  const refreshMetrics = () => api.metrics().then(setMetrics).catch(() => {});

  const launchSingle = async (target: string, params: Record<string, any>) => {
    if (!selected) return;
    resetRunState(false);
    try {
      const res = await api.launch(selected.id, target, params);
      setCorrelationId(res.correlation_id);
    } catch (e: any) {
      setError(e.message || String(e));
      setLaunching(false);
      setStatus(null);
    }
  };

  const launchCampaign = async () => {
    if (!selectedScenario) return;
    resetRunState(true);
    try {
      const res = await api.launchCampaign(selectedScenario);
      setCorrelationId(res.campaign_id);
      api.campaign(res.campaign_id).then(setCampaign).catch(() => {});
    } catch (e: any) {
      setError(e.message || String(e));
      setLaunching(false);
      setStatus(null);
    }
  };

  const resetRunState = (campaignMode: boolean) => {
    setError(null);
    setLaunching(true);
    setStatus("running");
    setExplanation(null);
    setActiveDefense(null);
    setCampaign(null);
    setIsCampaign(campaignMode);
  };

  const openHistory = (run: AttackRun) => {
    setMode("single");
    setIsCampaign(false);
    setSelectedId(run.attack_type);
    setCorrelationId(run.correlation_id);
    setStatus(run.status);
    setExplanation(run.ai_explanation);
    setActiveDefense(run.defense || null);
    setLaunching(false);
  };

  const reportUrl = isCampaign && correlationId
    ? api.campaignReportUrl(correlationId)
    : correlationId
      ? api.reportUrl(correlationId)
      : null;

  return (
    <div className="app">
      <div className="topbar">
        <div className="logo"><span className="cy">Cyber</span><span className="sim">Sim</span></div>
        <span className="tag">Ethical Attack Simulator</span>
        <span className="tag">
          <span className={`dot ${connected ? "on" : "off"}`} />
          {connected ? "WebSocket live" : "WebSocket idle"}
        </span>
        <PWAInstall />
        <span className="badge-lab">LOCAL LAB ONLY</span>
      </div>

      <MetricsStrip metrics={metrics} />

      <TargetShowcase />

      <ImpactMap
        metrics={metrics}
        history={history}
        events={events}
        selectedAttack={selectedId}
        defense={defenseView}
        campaign={campaign}
        isCampaign={isCampaign}
      />

      {error && (
        <div className="panel" style={{ borderColor: "var(--err)", marginBottom: 16 }}>
          <strong style={{ color: "var(--err)" }}>Error:</strong> {error}
        </div>
      )}

      <div className="tabs">
        <button className={`tab ${mode === "single" ? "active" : ""}`} onClick={() => setMode("single")}>
          Single Attack
        </button>
        <button className={`tab ${mode === "scenario" ? "active" : ""}`} onClick={() => setMode("scenario")}>
          Guided Scenario
        </button>
      </div>

      <div className="grid">
        <div>
          {mode === "single" ? (
            <>
              <AttackSelector modules={modules} selected={selectedId} onSelect={(id) => {
                setSelectedId(id);
                setActiveDefense(null);
              }} />
              <div style={{ height: 16 }} />
              <LaunchPanel module={selected} launching={launching} onLaunch={launchSingle} />
            </>
          ) : (
            <ScenarioPanel
              scenarios={scenarios}
              selected={selectedScenario}
              running={launching}
              onSelect={setSelectedScenario}
              onLaunch={launchCampaign}
            />
          )}
        </div>

        <div>
          <div className="panel">
            <div className="section-title">
              <h2 style={{ margin: 0 }}>Live {isCampaign ? "Campaign" : "Attack"}</h2>
              <div className="spacer" />
              <StatusIndicator status={status} />
            </div>
            <ProgressBar value={progress} />
            <div style={{ height: 12 }} />
            <LiveLogs events={events} />
            <div style={{ height: 12 }} />
            {reportUrl && (
              <a
                className="btn ghost"
                href={reportUrl}
                target="_blank"
                rel="noreferrer"
                style={status === "running" ? { pointerEvents: "none", opacity: 0.5 } : undefined}
              >
                Download {isCampaign ? "Campaign" : "PDF"} Report
              </a>
            )}
          </div>

          <div style={{ height: 16 }} />

          <div className="panel">
            <h2>{isCampaign ? "Campaign Steps" : "AI Explainer"}</h2>
            {isCampaign ? (
              <CampaignProgress campaign={campaign} />
            ) : (
              <AIExplainer explanation={explanation} />
            )}
          </div>

          <div style={{ height: 16 }} />
          <DefensePanel playbook={defenseView} />

          <div style={{ height: 16 }} />
          <RemediationLab guide={remediationView} />
        </div>
      </div>

      <div style={{ height: 16 }} />
      <HistoryPanel runs={history} onOpen={openHistory} />

      <p className="muted" style={{ textAlign: "center", marginTop: 20 }}>
        CyberSim - For authorized security education and defensive testing only -
        All attacks confined to isolated Docker containers.
      </p>
    </div>
  );
}
