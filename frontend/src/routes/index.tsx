import { Link } from "@tanstack/react-router";
import { UrlInputBar } from "../components/UrlInputBar";
import { SiteHeader } from "../components/SiteHeader";

export function IndexRoute() {
  return <div className="site-shell"><SiteHeader /><main className="page-wrap"><section className="report-section"><div className="eyebrow">PUBLIC WEBSITE INSPECTION</div><h1 className="hero-title">WEBLOGIST</h1><p className="hero-copy">A straight report of the technologies, routes, SEO signals, and performance signals visible from the public surface of any website.</p><UrlInputBar /></section><section className="landing-notes"><div className="landing-note"><strong>Tech stack</strong><span>Evidence-backed technology findings with confidence scores.</span></div><div className="landing-note"><strong>API routes</strong><span>Paths surfaced from public HTML and same-origin assets.</span></div><div className="landing-note"><strong>Site signals</strong><span>SEO metadata, timing, page weight, and render blockers.</span></div></section></main><footer className="site-footer">WEBLOGIST · PUBLIC-SIGNAL REPORTING · <Link to="/" className="text-[#ffb703]">START AN INSPECTION</Link></footer></div>;
}
