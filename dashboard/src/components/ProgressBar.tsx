export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="progress" title={`${value}%`}>
      <div style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}
