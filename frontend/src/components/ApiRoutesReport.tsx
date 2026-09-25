import type { ApiRoute } from "../lib/types";

export function ApiRoutesReport({ routes }: { routes?: ApiRoute[] }) {
  const items = routes || [];
  return <section className="report-section api-report"><div className="section-heading"><div><h2>API ROUTES</h2><p>Paths surfaced from public HTML and same-origin bundles.</p></div></div><div className="panel"><div className="tree-list"><div className="tree-route"><span className="text-[#9584a2]">/</span></div>{items.length ? items.map((route, index) => <div className="tree-route" key={`${route.path}-${route.method_guess}`}><span className="tree-connector">{index === items.length - 1 ? "└─" : "├─"}</span><span className="method-tag">{route.method_guess}</span><span>{route.path}</span></div>) : <p className="no-findings">No API routes identified from public signals.</p>}</div></div></section>;
}
