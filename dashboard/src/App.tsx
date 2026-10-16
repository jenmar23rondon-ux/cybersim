import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { RotateCcw } from "lucide-react";
import { api } from "./api";
import { readLabBoundary, saveLabBoundary } from "./labSession";
import type { AttackModule, AttackRun, Campaign, LabBoundary, Metrics, RemediationGuide, Scenario } from "./types";
import { useAttackSocket } from "./hooks/useWebSocket";
import { AttackSelector } from "./components/AttackSelector";
import { LaunchPanel } from "./components/LaunchPanel";
import { LiveLogs } from "./components/LiveLogs";
import { LiveNarrative } from "./components/LiveNarrative";
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
import { TargetConnector } from "./components/TargetConnector";

type Status = "running" | "success" | "failed";
type Mode = "single" | "scenario";
const CLOUD_TARGET_URL = import.meta.env.VITE_CLOUD_TARGET_URL || "";

export default function App() {
  const [mode, setMode] = useState<Mode>("single");
  const [modules, setModules] = useState<AttackModule[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [launching, setLaunching] = useState(false);
  const [correlationId, setCorrelationId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [activeRun, setActiveRun] = useState<AttackRun | null>(null);
  const [history, setHistory] = useState<AttackRun[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [remediationGuides, setRemediationGuides] = useState<RemediationGuide[]>([]);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [campaignRuns, setCampaignRuns] = useState<AttackRun[]>([]);
  const [isCampaign, setIsCampaign] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [historyNotice, setHistoryNotice] = useState<{ text: string; error?: boolean } | null>(null);
  const [resetting, setResetting] = useState(false);
  const [boundary, setBoundary] = useState<LabBoundary | null>(readLabBoundary);
  const [formVersion, setFormVersion] = useState(0);
  const viewVersion = useRef(0);
  const [connectedTarget, setConnectedTarget] = useState<{ host: string; port: number; scheme?: string } | null>(null);
  const [runAttackId, setRunAttackId] = useState<string | null>(null);

  const { events: socketEvents, connected } = useAttackSocket(correlationId);
  const selected = modules.find((m) => m.id === selectedId) || null;
  const attackName = modules.find((m) => m.id === runAttackId)?.name || selected?.name;
  const defenseView = activeRun?.defense || null;
  const remediationView = remediationGuides.find((g) => g.attack_type === runAttackId) || null;
  const events = useMemo(() => {
    const stored = isCampaign ? campaignRuns.flatMap((run) => run.logs) : activeRun?.logs || [];
    const merged = new Map([...stored, ...socketEvents].map((event) => [
      `${event.correlation_id}:${event.timestamp}:${event.message}`, event,
    ]));
    return [...merged.values()].sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  }, [activeRun, campaignRuns, isCampaign, socketEvents]);
  const progress = status === "success" || status === "failed" ? 100
    : events.length ? events[events.length - 1].progress : 0;

  const refreshHistory = useCallback(async () => {
    const version = viewVersion.current;
    try {
      const runs = await api.history(boundary);
      if (viewVersion.current === version) setHistory(runs);
    } catch (e) {
      if (viewVersion.current === version) setError(String(e));
    }
  }, [boundary]);
  const refreshMetrics = useCallback(async () => {
    const version = viewVersion.current;
    try {
      const value = await api.metrics(boundary);
      if (viewVersion.current === version) setMetrics(value);
    } catch (e) {
      if (viewVersion.current === version) setError(String(e));
    }
  }, [boundary]);

  useEffect(() => {
    let disposed = false;
    api.modules().then((value) => {
      if (disposed) return;
      setModules(value);
      if (value.length) setSelectedId(value[0].id);
    }).catch((e) => { if (!disposed) setError(String(e)); });
    api.scenarios().then((value) => {
      if (disposed) return;
      setScenarios(value);
      if (value.length) setSelectedScenario(value[0].id);
    }).catch(() => {});
    api.remediationGuides().then((value) => {
      if (!disposed) setRemediationGuides(value);
    }).catch(() => {});
    return () => { disposed = true; };
  }, []);

  useEffect(() => {
    refreshMetrics();
    refreshHistory();
  }, [refreshMetrics, refreshHistory]);

  useEffect(() => {
    if (!correlationId) return;
    let stopped = false;
    let inFlight = false;
    const version = viewVersion.current;
    const current = () => !stopped && viewVersion.current === version;
    const poll = async () => {
      if (inFlight || !current()) return;
      inFlight = true;
      try {
        if (isCampaign) {
          const value = await api.campaign(correlationId);
          if (!current()) return;
          setError(null);
          setCampaign(value);
          setStatus(value.status);
          setLaunching(value.status === "running");
          const snapshots = await Promise.all(value.steps.filter((step) => step.correlation_id)
            .map((step) => api.run(step.correlation_id!)));
          if (!current()) return;
          setCampaignRuns(snapshots);
          const latest = snapshots[snapshots.length - 1];
          setActiveRun(latest || null);
          setRunAttackId(latest?.attack_type || null);
          if (value.status !== "running") stopped = true;
        } else {
          const value = await api.run(correlationId);
          if (!current()) return;
          setError(null);
          setActiveRun(value);
          setStatus(value.status);
          setLaunching(value.status === "running");
          if (value.status !== "running") stopped = true;
        }
        if (stopped) {
          refreshHistory();
          refreshMetrics();
          window.clearInterval(timer);
        }
      } catch (e) {
        if (current()) setError(String(e));
      } finally {
        inFlight = false;
      }
    };
    const timer = window.setInterval(poll, 3000);
    poll();
    return () => { stopped = true; window.clearInterval(timer); };
  }, [correlationId, isCampaign, refreshHistory, refreshMetrics]);

  const clearRun = (campaignMode = false) => {
    viewVersion.current += 1;
    setCorrelationId(null);
    setError(null);
    setNotice(null);
    setHistoryNotice(null);
    setStatus(null);
    setActiveRun(null);
    setRunAttackId(null);
    setCampaign(null);
    setCampaignRuns([]);
    setIsCampaign(campaignMode);
    setLaunching(false);
  };
  const launchSingle = async (target: string, params: Record<string, any>) => {
    if (!selected || launching || resetting) return;
    clearRun();
    const version = viewVersion.current;
    setRunAttackId(selected.id);
    setLaunching(true);
    setStatus("running");
    try {
      const res = await api.launch(selected.id, target, params);
      if (viewVersion.current === version) setCorrelationId(res.correlation_id);
    } catch (e: any) {
      if (viewVersion.current !== version) return;
      setError(e.message || String(e));
      setLaunching(false);
      setStatus(null);
      setRunAttackId(null);
    }
  };
  const launchCampaign = async () => {
    if (!selectedScenario || launching || resetting) return;
    clearRun(true);
    const version = viewVersion.current;
    setLaunching(true);
    setStatus("running");
    try {
      const res = await api.launchCampaign(selectedScenario);
      if (viewVersion.current === version) setCorrelationId(res.campaign_id);
    } catch (e: any) {
      if (viewVersion.current !== version) return;
      setError(e.message || String(e));
      setLaunching(false);
      setStatus(null);
    }
  };
  const openHistory = (run: AttackRun) => {
    if (launching || resetting) return;
    clearRun();
    setMode("single");
    setSelectedId(run.attack_type);
    setCorrelationId(run.correlation_id);
    setStatus(run.status);
    setActiveRun(run);
    setRunAttackId(run.attack_type);
    setLaunching(run.status === "running");
  };
  const resetLab = async (scope: "lab" | "reports" = "lab") => {
    if (resetting || (scope === "reports" && launching)) return;
    const reportsOnly = scope === "reports";
    const message = (reportsOnly
      ? "¿Reiniciar los informes? Se vaciarán el historial visible, sus contadores y los resultados abiertos para mostrar los informes nuevos. La configuración de la prueba se conservará. "
      : "¿Reiniciar la sesión del laboratorio? Se pondrán en cero los contadores, el historial visible y los paneles. ")
      + "Los informes anteriores seguirán guardados."
      + (launching ? " La prueba en curso seguirá ejecutándose en el backend." : "");
    if (!window.confirm(message)) return;
    setResetting(true);
    try {
      const next = await api.labBaseline();
      saveLabBoundary(next);
      clearRun();
      setBoundary(next);
      setHistory([]);
      setMetrics(null);
      if (reportsOnly) {
        setHistoryNotice({ text: "Informes reiniciados. Los nuevos resultados aparecerán aquí; los PDF anteriores siguen guardados." });
      } else {
        setMode("single");
        setSelectedId(null);
        setSelectedScenario(null);
        setFormVersion((value) => value + 1);
        setNotice("Sesión reiniciada. Contadores y resultados en cero; los informes anteriores siguen guardados.");
      }
    } catch (e: any) {
      if (reportsOnly) setHistoryNotice({ text: `No se pudieron reiniciar los informes: ${e.message || String(e)}`, error: true });
      else setError(`No se pudo reiniciar la sesión: ${e.message || String(e)}`);
    } finally { setResetting(false); }
  };
  const reportUrl = correlationId ? isCampaign ? api.campaignReportUrl(correlationId)
    : api.reportUrl(correlationId) : null;

  return (
    <div className="app">
      <div className="topbar">
        <div className="logo"><span className="cy">Cyber</span><span className="sim">Sim</span></div>
        <span className="tag">Ethical Attack Simulator</span>
        <span className="tag"><span className={`dot ${connected ? "on" : "off"}`} />
          {connected ? "WebSocket live" : "WebSocket idle"}</span>
        <PWAInstall />
        <button className="btn ghost compact reset-btn" type="button" onClick={() => resetLab()} disabled={resetting || (launching && !correlationId)}
          title="Reiniciar la sesión del laboratorio">
          <RotateCcw size={16} aria-hidden="true" /> {resetting ? "Reiniciando..." : "Reset lab"}
        </button>
        <span className="badge-lab">LOCAL LAB ONLY</span>
      </div>
      {notice && <p className="session-notice" role="status">{notice}</p>}
      <MetricsStrip metrics={metrics} />
      <TargetShowcase cloudTargetUrl={CLOUD_TARGET_URL} onUseCloudTarget={(target) => {
        setMode("single"); setSelectedId("phishing_sim"); setConnectedTarget(target);
      }} />
      <ImpactMap metrics={metrics} history={history} events={events} selectedAttack={runAttackId}
        defense={defenseView} campaign={campaign} campaignRuns={campaignRuns} isCampaign={isCampaign} />
      {error && <div className="panel" role="alert" style={{ borderColor: "var(--err)", marginBottom: 16 }}>
        <strong style={{ color: "var(--err)" }}>Error:</strong> {error}</div>}
      <div className="tabs">
        <button className={`tab ${mode === "single" ? "active" : ""}`} onClick={() => setMode("single")}>Single Attack</button>
        <button className={`tab ${mode === "scenario" ? "active" : ""}`} onClick={() => setMode("scenario")}>Guided Scenario</button>
      </div>
      <div className="grid">
        <div>
          {mode === "single" ? <>
            <AttackSelector modules={modules} selected={selectedId} onSelect={setSelectedId} />
            <div style={{ height: 16 }} />
            <LaunchPanel key={formVersion} module={selected} launching={launching || resetting}
              targetOverride={connectedTarget} onLaunch={launchSingle} />
            <div style={{ height: 16 }} /><TargetConnector key={formVersion} onApply={setConnectedTarget} />
          </> : <ScenarioPanel scenarios={scenarios} selected={selectedScenario} running={launching || resetting}
            onSelect={setSelectedScenario} onLaunch={launchCampaign} />}
        </div>
        <div>
          <div className="panel">
            <div className="section-title">
              <h2 style={{ margin: 0 }}>Live {isCampaign ? "Campaign" : "Attack"}</h2>
              <div className="spacer" /><StatusIndicator status={status} />
            </div>
            <ProgressBar value={progress} />
            <div style={{ height: 12 }} /><LiveLogs events={events} />
            <div style={{ height: 12 }} /><LiveNarrative events={events} defense={defenseView} remediation={remediationView} />
            {reportUrl && <a className="btn ghost" href={reportUrl} target="_blank" rel="noreferrer"
              style={status === "running" ? { pointerEvents: "none", opacity: 0.5 } : undefined}>
              Download {isCampaign ? "Campaign" : "PDF"} Report</a>}
          </div>
          <div style={{ height: 16 }} />
          <div className="panel">
            <h2>{isCampaign ? "Campaign Steps" : "AI Explainer"}</h2>
            {isCampaign ? <CampaignProgress campaign={campaign} runs={campaignRuns} />
              : <AIExplainer explanation={activeRun?.ai_explanation || null} />}
          </div>
          <div style={{ height: 16 }} />
          <DefensePanel playbook={defenseView} attackName={attackName} running={launching} />
          <div style={{ height: 16 }} /><RemediationLab guide={remediationView} />
        </div>
      </div>
      <div style={{ height: 16 }} /><HistoryPanel runs={history} onOpen={openHistory} disabled={launching || resetting}
        onReset={() => resetLab("reports")} resetting={resetting} resetDisabled={launching || resetting} notice={historyNotice} />
      <p className="muted" style={{ textAlign: "center", marginTop: 20 }}>
        CyberSim - For authorized security education and defensive testing only - All attacks confined to isolated Docker containers.
      </p>
    </div>
  );
}
