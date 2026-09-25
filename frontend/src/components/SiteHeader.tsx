import { Link } from "@tanstack/react-router";

export function SiteHeader() {
  return <header className="topbar"><div className="topbar-inner"><Link to="/" className="flex items-center gap-3"><span className="brand-mark">DS</span><span className="pixel text-[11px] text-parchment">DIG SITE</span></Link><span className="hidden text-[18px] text-[#c5b8c9] sm:block">PUBLIC SIGNAL REPORTING</span></div></header>;
}
