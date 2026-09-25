import type { TechItem, TechStack } from "../lib/types";

const categories: Array<{ key: keyof TechStack; label: string }> = [
  { key: "frontend", label: "Frontend frameworks and libraries" },
  { key: "backend", label: "Server-side frameworks" },
  { key: "languages", label: "Client-side languages" },
  { key: "server_runtime", label: "Server-side language/runtime signals" },
  { key: "styling", label: "Styling" },
  { key: "hosting", label: "Hosting, web server, and CDN" },
  { key: "tooling", label: "Build tooling" },
  { key: "analytics", label: "Analytics" },
];
const icons: Record<string, string> = {
  "React": "⚛", "Vue.js": "◉", "Svelte": "◈", "Angular": "A", "Next.js": "N",
  "jQuery": "$", "Express.js": "E", "Laravel": "L", "Django": "D", "Ruby on Rails": "R",
  "WordPress": "W", "JavaScript": "JS", "TypeScript": "TS", "PHP": "PHP", "Node.js": "N",
  "C# / .NET": ".NET", "Nginx": "N", "Apache": "A", "Cloudflare": "C", "Vercel": "▲",
  "Tailwind CSS": "T", "Bootstrap": "B", "Vite": "⚡", "Webpack": "W",
};
const tier = (confidence: TechItem["confidence"]) => confidence === "high" ? "legendary" : confidence === "medium" ? "rare" : "cursed";
const tierLabel = (confidence: TechItem["confidence"]) => confidence === "high" ? "LEGENDARY" : confidence === "medium" ? "RARE" : "CURSED RELIC";

function Finding({ item, category }: { item: TechItem; category: string }) {
  const kind = tier(item.confidence);
  const score = Math.round(Math.max(0, Math.min(1, item.score)) * 100);
  return <article className={`loot-card ${kind}`}><span className={`tier-chip ${kind}`}>{tierLabel(item.confidence)}</span><span className="loot-icon" aria-hidden="true">{icons[item.name] || "◇"}</span><strong className="loot-name">{item.name}</strong><span className="loot-category">{category}</span><span className="loot-score">Evidence {score}/100</span>{item.confidence === "low" && <span className="cursed-note">unable to determine</span>}<details className="evidence"><summary>Why we think this</summary><ul className="evidence-list">{(item.evidence_items?.length ? item.evidence_items.map((evidence, index) => <li key={`${evidence.signature}-${index}`}>{evidence.explanation} <span>Source: {evidence.source}</span></li>) : item.evidence.map((line, index) => <li key={index}>{line}</li>))}</ul></details></article>;
}

export function TechStackReport({ tech }: { tech: TechStack }) {
  return <div className="tech-report flex flex-col gap-8">{categories.map(({ key, label }) => { const items = tech[key] || []; return <section className="report-section" key={key}><div className="section-heading"><div><h2>{label.toUpperCase()}</h2><p>{key === "backend" ? "Public signals only; hidden server frameworks may be undetectable." : "Signals collected from public responses and assets."}</p></div></div>{items.length ? <div className="loot-grid">{items.map((item) => <Finding key={`${key}-${item.name}`} item={item} category={label} />)}</div> : <p className={`no-findings ${key === "backend" || key === "server_runtime" ? "cursed" : ""}`}>{key === "backend" ? "No server-side framework identified from public signals." : key === "server_runtime" ? "No server-side runtime identified from public signals." : "No clear signal detected."}</p>}</section>; })}</div>;
}
