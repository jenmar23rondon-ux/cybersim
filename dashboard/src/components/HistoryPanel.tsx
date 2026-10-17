import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Check, ChevronDown, ChevronRight, Copy, Download, RefreshCw, RotateCcw, Search, X } from "lucide-react";
import type { AttackRun } from "../types";
import { api } from "../api";
import { AnalystReview } from "./AnalystReview";

interface Props {
  runs: AttackRun[];
  onOpen: (run: AttackRun) => void;
  onRefresh: () => Promise<unknown>;
  disabled?: boolean;
  onReset: () => Promise<boolean>;
  resetting: boolean;
  resetDisabled: boolean;
  notice: { text: string; error?: boolean } | null;
}

const FILTERS = [
  ["all", "All results"], ["finding", "Findings"], ["inconclusive", "Needs review"],
  ["simulation", "Simulations"], ["observation", "Observations"],
  ["no_finding", "No findings"], ["pending", "Running"],
] as const;
type Filter = typeof FILTERS[number][0];
type Sort = "newest" | "oldest" | "risk";
const OUTCOMES: Record<string, string> = Object.fromEntries(FILTERS.slice(1));

function outcomeFor(run: AttackRun) {
  return run.defense?.analyst_review?.outcome || (run.status === "running" ? "pending" : "inconclusive");
}

function timestamp(value: string | null) {
  return value && Number.isFinite(Date.parse(value)) ? new Date(value).toLocaleString() : "Not recorded";
}

export function HistoryPanel({ runs, onOpen, onRefresh, disabled, onReset, resetting, resetDisabled, notice }: Props) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [sort, setSort] = useState<Sort>("newest");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [feedback, setFeedback] = useState<{ id: string; copied: boolean } | null>(null);
  const filtered = Boolean(query.trim()) || filter !== "all";

  const visible = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    const matches = runs.filter((run) => {
      const searchable = [run.attack_type, run.target, run.correlation_id,
        run.defense?.analyst_review?.decision, OUTCOMES[outcomeFor(run)]].join(" ").toLocaleLowerCase();
      return (!term || searchable.includes(term)) && (filter === "all" || outcomeFor(run) === filter);
    });
    return matches.sort((a, b) => sort === "risk"
      ? (b.defense?.risk_score ?? 0) - (a.defense?.risk_score ?? 0) || b.id - a.id
      : sort === "oldest" ? a.id - b.id : b.id - a.id);
  }, [runs, query, filter, sort]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => setFeedback(null), 3000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  const clearFilters = () => { setQuery(""); setFilter("all"); };
  const reset = async () => {
    if (await onReset()) {
      clearFilters();
      setSort("newest");
      setExpanded(null);
      setFeedback(null);
    }
  };
  const refresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    try { await onRefresh(); } finally { setRefreshing(false); }
  };
  const copyId = async (id: string) => {
    try {
      await navigator.clipboard.writeText(id);
      setFeedback({ id, copied: true });
    } catch { setFeedback({ id, copied: false }); }
  };

  return (
    <section className="panel history-panel" aria-labelledby="history-title">
      <div className="section-title history-heading">
        <h2 id="history-title">Attack History <span className="history-count">{runs.length}</span></h2>
        <div className="history-actions">
          <button className="history-icon" type="button" onClick={refresh} disabled={refreshing || resetting}
            aria-label="Refresh reports" title="Refresh reports" aria-busy={refreshing}>
            <RefreshCw size={16} className={refreshing ? "history-spinning" : ""} aria-hidden="true" />
          </button>
          <button className="btn ghost compact history-reset" type="button" onClick={reset}
            disabled={resetDisabled || refreshing} aria-busy={resetting}
            title={disabled && !resetting ? "Wait for the current test to finish" : "Reset the reports shown in this session"}>
            <RotateCcw size={16} aria-hidden="true" />
            {resetting ? "Resetting..." : "Reset reports"}
          </button>
        </div>
      </div>
      {notice && <p className={`history-notice ${notice.error ? "error" : ""}`} role={notice.error ? "alert" : "status"}>{notice.text}</p>}

      <div className="history-toolbar">
        <div className="history-search">
          <Search size={16} aria-hidden="true" />
          <input type="search" aria-label="Search reports" placeholder="Search reports..." value={query}
            onChange={(event) => setQuery(event.target.value)} />
          {query && <button type="button" className="history-icon" aria-label="Clear search" title="Clear search"
            onClick={() => setQuery("")}><X size={14} aria-hidden="true" /></button>}
        </div>
        <select aria-label="Filter reports by result" value={filter} onChange={(event) => setFilter(event.target.value as Filter)}>
          {FILTERS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select aria-label="Sort reports" value={sort} onChange={(event) => setSort(event.target.value as Sort)}>
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="risk">Highest risk</option>
        </select>
      </div>
      <div className="history-results" role="status" aria-atomic="true">
        <span>{visible.length} of {runs.length} reports</span>
        {filtered && <button className="history-clear" type="button" onClick={clearFilters}>
          <X size={13} aria-hidden="true" /> Clear filters
        </button>}
      </div>

      {visible.length === 0 && <p className="muted history-empty">
        {runs.length ? "No reports match these filters." : "No reports in this session yet."}
      </p>}
      {visible.map((run) => {
        const open = expanded === run.correlation_id;
        const outcome = outcomeFor(run);
        const review = run.defense?.analyst_review;
        const copied = feedback?.id === run.correlation_id && feedback.copied;
        const detailId = `report-details-${run.id}`;
        return (
          <article className={`history-item ${open ? "expanded" : ""}`} key={run.id}>
            <div className="hist-row">
              <button className="history-open" type="button" aria-expanded={open} aria-controls={detailId}
                aria-label={`${open ? "Hide" : "Show"} report details for ${run.attack_type}`}
                onClick={() => { setExpanded(open ? null : run.correlation_id); setFeedback(null); }}>
                {open ? <ChevronDown size={16} aria-hidden="true" /> : <ChevronRight size={16} aria-hidden="true" />}
                <span className="history-identity">
                  <span className="type">{run.attack_type}</span>
                  <span className="meta">{run.target} · {timestamp(run.started_at)}</span>
                </span>
              </button>
              <span className={`history-outcome ${outcome}`}>{OUTCOMES[outcome] || "Needs review"}</span>
              <span className="history-risk" title="Risk score">{run.defense ? `${run.defense.risk_score}/100` : "-"}</span>
              <a className="history-icon" href={api.reportUrl(run.correlation_id)} target="_blank" rel="noreferrer"
                aria-label={`Download PDF for ${run.attack_type}`} title="Download PDF"
                aria-disabled={run.status === "running"}
                onClick={(event) => { if (run.status === "running") event.preventDefault(); }}>
                <Download size={16} aria-hidden="true" />
              </a>
            </div>
            {open && <div className="history-detail" id={detailId}>
              <dl className="history-metadata">
                <div><dt>Execution</dt><dd>{run.status}</dd></div>
                <div><dt>Started</dt><dd>{timestamp(run.started_at)}</dd></div>
                <div><dt>Finished</dt><dd>{timestamp(run.finished_at)}</dd></div>
                <div><dt>Run ID</dt><dd className="history-run-id"><code>{run.correlation_id}</code>
                  <button className="history-icon" type="button" onClick={() => copyId(run.correlation_id)}
                    title="Copy run ID" aria-label="Copy run ID">
                    {copied ? <Check size={15} aria-hidden="true" /> : <Copy size={15} aria-hidden="true" />}
                  </button>
                </dd></div>
              </dl>
              {feedback?.id === run.correlation_id && <p className="history-copy-status" role="status">
                {feedback.copied ? "Run ID copied." : "Could not copy. Select the run ID to copy it manually."}
              </p>}
              {review ? <AnalystReview review={review} /> : <p className="muted">Analyst review is not available for this result.</p>}
              <button className="btn ghost compact history-full-report" type="button" disabled={disabled}
                onClick={() => onOpen(run)}><ArrowUpRight size={16} aria-hidden="true" /> Open full report</button>
            </div>}
          </article>
        );
      })}
    </section>
  );
}
