import type { IconType } from "react-icons";
import { SiAngular, SiApache, SiBootstrap, SiCloudflare, SiDjango, SiDotnet, SiExpress, SiFirebase, SiJavascript, SiJquery, SiLaravel, SiNetlify, SiNextdotjs, SiNginx, SiNodedotjs, SiPhp, SiPostgresql, SiReact, SiRubyonrails, SiSupabase, SiSvelte, SiTailwindcss, SiTypescript, SiVercel, SiVite, SiVuedotjs, SiWebpack, SiWordpress } from "react-icons/si";
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
const icons: Record<string, IconType> = {
  React: SiReact, "Vue.js": SiVuedotjs, Svelte: SiSvelte, Angular: SiAngular, "Next.js": SiNextdotjs, jQuery: SiJquery,
  "Express.js": SiExpress, Laravel: SiLaravel, Django: SiDjango, "Ruby on Rails": SiRubyonrails, WordPress: SiWordpress,
  JavaScript: SiJavascript, TypeScript: SiTypescript, PHP: SiPhp, "Node.js": SiNodedotjs, "C# / .NET": SiDotnet,
  Nginx: SiNginx, Apache: SiApache, Cloudflare: SiCloudflare, Vercel: SiVercel, Netlify: SiNetlify,
  "Tailwind CSS": SiTailwindcss, Bootstrap: SiBootstrap, Vite: SiVite, Webpack: SiWebpack, Supabase: SiSupabase, Firebase: SiFirebase, PostgreSQL: SiPostgresql,
};
const tier = (confidence: TechItem["confidence"]) => confidence === "high" ? "legendary" : confidence === "medium" ? "rare" : "cursed";
const tierLabel = (confidence: TechItem["confidence"]) => confidence === "high" ? "LEGENDARY" : confidence === "medium" ? "RARE" : "CURSED RELIC";

function Finding({ item, category }: { item: TechItem; category: string }) {
  const kind = tier(item.confidence);
  const score = Math.round(Math.max(0, Math.min(1, item.score)) * 100);
  const Icon = icons[item.name];
  return <article className={`loot-card ${kind}`}><span className={`tier-chip ${kind}`}>{tierLabel(item.confidence)}</span><span className="loot-icon" aria-hidden="true">{Icon ? <Icon /> : <span className="text-[20px] font-bold text-parchment">{item.name.slice(0, 2).toUpperCase()}</span>}</span><strong className="loot-name">{item.name}</strong><span className="loot-category">{category}</span><span className="loot-score">Evidence {score}/100</span>{item.confidence === "low" && <span className="cursed-note">unable to determine</span>}<details className="evidence"><summary>Why we think this</summary><ul className="evidence-list">{(item.evidence_items?.length ? item.evidence_items.map((evidence, index) => <li key={`${evidence.signature}-${index}`}>{evidence.explanation} <span>Source: {evidence.source}</span></li>) : item.evidence.map((line, index) => <li key={index}>{line}</li>))}</ul></details></article>;
}

export function TechStackReport({ tech }: { tech: TechStack }) {
  return <div className="tech-report flex flex-col gap-8">{categories.map(({ key, label }) => { const items = tech[key] || []; return <section className="report-section" key={key}><div className="section-heading"><div><h2>{label.toUpperCase()}</h2><p>{key === "backend" ? "Public signals only; hidden server frameworks may be undetectable." : "Signals collected from public responses and assets."}</p></div></div>{items.length ? <div className="loot-grid">{items.map((item) => <Finding key={`${key}-${item.name}`} item={item} category={label} />)}</div> : <p className={`no-findings ${key === "backend" || key === "server_runtime" ? "cursed" : ""}`}>{key === "backend" ? "No server-side framework identified from public signals." : key === "server_runtime" ? "No server-side runtime identified from public signals." : "No clear signal detected."}</p>}</section>; })}</div>;
}
