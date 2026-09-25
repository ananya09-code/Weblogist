import type { ScanResult } from "../lib/types";

function value(record: Record<string, unknown>, key: string) { const parsed = Number(record[key] || 0); return Number.isFinite(parsed) ? parsed : 0; }
function Metric({ label, amount, unit, ratio, verdict, tone }: { label: string; amount: number; unit: string; ratio: number; verdict: string; tone: "good" | "rare" | "cursed" }) {
  return <div className="metric-row"><div className="metric-label"><span>{label}</span><span>{amount}{unit}</span></div><div className="metric-track"><div className={`metric-fill ${tone}`} style={{ width: `${Math.max(2, Math.min(100, ratio))}%` }} /></div><p className={`metric-verdict ${tone}`}>{verdict}</p></div>;
}
function KeyRow({ label, value }: { label: string; value: React.ReactNode }) { return <div className="key-row"><dt>{label}</dt><dd>{value || "—"}</dd></div>; }
export function SeoPerformanceReport({ result }: { result: ScanResult }) {
  const seo = result.seo as Record<string, unknown>;
  const performance = result.performance as Record<string, unknown>;
  const ttfb = value(performance, "ttfb_ms");
  const weight = value(performance, "total_page_weight_kb");
  const blocking = value(performance, "render_blocking_scripts");
  return <section className="report-section stats-report"><div className="section-heading"><div><h2>SEO & PERFORMANCE</h2><p>Metadata and measured page behavior from the public scan.</p></div></div><div className="panel character-sheet"><div className="sheet-block"><h3>SEO SIGNALS</h3><dl><KeyRow label="Title" value={seo.title as string} /><KeyRow label="Description" value={seo.meta_description as string} /><KeyRow label="Canonical" value={seo.canonical as string} /><KeyRow label="Robots" value={seo.robots_status as string} /></dl></div><div className="sheet-block"><h3>PERFORMANCE READOUT</h3><dl><Metric label="TTFB" amount={ttfb} unit=" ms" ratio={ttfb / 8} verdict={ttfb <= 300 ? "reasonable — no major server delay" : ttfb <= 800 ? "watch — worth investigating" : "sluggish — worth investigating"} tone={ttfb <= 300 ? "good" : ttfb <= 800 ? "rare" : "cursed"} /><Metric label="Page weight" amount={weight} unit=" KB" ratio={weight / 20} verdict={weight <= 500 ? "reasonable — lightweight page" : weight <= 1500 ? "watch — room to trim" : "heavy — worth investigating"} tone={weight <= 500 ? "good" : weight <= 1500 ? "rare" : "cursed"} /><Metric label="Render blocking" amount={blocking} unit=" scripts" ratio={blocking * 20} verdict={blocking === 0 ? "no blockers found" : blocking <= 2 ? "a few blockers found" : "several blockers found"} tone={blocking === 0 ? "good" : blocking <= 2 ? "rare" : "cursed"} /></dl></div></div></section>;
}
