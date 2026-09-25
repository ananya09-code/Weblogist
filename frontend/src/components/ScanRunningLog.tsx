export function ScanRunningLog({ status }: { status: string }) {
  const lines = status === "queued" ? ["Resolving host…", "Waiting for inspection worker…"] : ["Resolving host…", "Checking headers…", "Inspecting public assets…", "Rendering with Playwright if needed…", "Building report…"];
  return <div className="log-panel" role="status" aria-live="polite"><div className="log-heading"><span className="log-dot" />{status === "queued" ? "SCAN QUEUED" : "SCAN IN PROGRESS"}</div>{lines.map((line) => <div className="log-line" key={line}><span>›</span><span>{line}</span></div>)}</div>;
}
