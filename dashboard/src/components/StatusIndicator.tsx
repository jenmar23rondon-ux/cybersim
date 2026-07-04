type Status = "running" | "success" | "failed";

const LABEL: Record<Status, string> = {
  running: "RUNNING",
  success: "SUCCESS - VULNERABLE",
  failed: "FAILED / NOT VULNERABLE",
};

export function StatusIndicator({ status }: { status: Status | null }) {
  if (!status) return null;
  return <span className={`pill ${status}`}>{LABEL[status]}</span>;
}
