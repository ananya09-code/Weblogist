import { Link, useParams } from "@tanstack/react-router";
import { useScan } from "../lib/api";
import { UrlInputBar } from "../components/UrlInputBar";
import { ScanRunningLog } from "../components/ScanRunningLog";
import { SiteHeader } from "../components/SiteHeader";
import { TechStackReport } from "../components/TechStackReport";
import { ApiRoutesReport } from "../components/ApiRoutesReport";
import { SeoPerformanceReport } from "../components/SeoPerformanceReport";

export function ScanRoute() {
  const { id } = useParams({ from: "/scans/$id" });
  const scan = useScan(id);
  const result = scan.data?.result;
  const isActive = scan.data?.status === "queued" || scan.data?.status === "running";
  return <div className="site-shell"><SiteHeader /><main className="page-wrap"><div className="report-header"><div><Link to="/" className="pixel text-[10px] text-[#ffb703]">← NEW INSPECTION</Link><p className="mt-4 text-[18px] text-[#b9aabd]">SCAN {id.slice(0, 8).toUpperCase()}</p><h1 className="report-title">{scan.data?.url || "WEBSITE ANALYSIS"}</h1></div>{scan.data?.status === "done" && <span className="status-chip">REPORT READY</span>}{scan.data?.status === "failed" && <span className="status-chip failed">SCAN FAILED</span>}</div><UrlInputBar />{scan.isError && <p className="form-error">Could not load this scan: {scan.error.message}</p>}{scan.isLoading && <ScanRunningLog status="queued" />}{scan.data?.status === "failed" && <div className="log-panel"><div className="log-heading">INSPECTION FAILED</div><p className="mb-0 mt-3 text-[19px] text-[#f08a68]">{scan.data.error || "The target could not be analyzed."}</p></div>}{isActive && <ScanRunningLog status={scan.data?.status || "queued"} />}{result && <><TechStackReport tech={result.tech_stack} /><ApiRoutesReport routes={result.api_routes} /><SeoPerformanceReport result={result} /></>}{scan.data?.status === "done" && !result && <div className="log-panel"><div className="log-heading">REPORT UNAVAILABLE</div><p className="mb-0 mt-3 text-[19px] text-[#f08a68]">The scan completed without a saved report. Start a new inspection to try again.</p></div>}</main><footer className="site-footer">EVIDENCE IS BASED ON PUBLIC SIGNALS · HIDDEN SERVER TECHNOLOGIES MAY NOT BE VISIBLE</footer></div>;
}
