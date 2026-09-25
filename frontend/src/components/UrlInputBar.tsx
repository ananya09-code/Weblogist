import { useState } from "react";
import { useCreateScan } from "../lib/api";
import { useNavigate } from "@tanstack/react-router";

export function UrlInputBar() {
  const [url, setUrl] = useState("");
  const create = useCreateScan();
  const navigate = useNavigate();

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!url.trim() || create.isPending) return;
    create.mutate(url.trim(), { onSuccess: (scan) => navigate({ to: "/scans/$id", params: { id: scan.scan_id } }) });
  }

  return <form className="border-y border-rule py-[18px]" onSubmit={submit}>
    <div className="mb-[11px] flex items-baseline justify-between gap-4 max-sm:block"><span className="text-sm font-bold">Inspect a website</span><span className="text-xs text-[#788079] max-sm:mt-1 max-sm:block">Public HTTP(S) URLs only</span></div>
    <div className="flex gap-[9px] max-sm:block"><label className="sr-only" htmlFor="url">Website URL</label><input id="url" type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com" required className="h-[43px] min-w-0 flex-1 border border-rule bg-white/35 px-3 text-ink outline-none focus:border-signal focus:ring-2 focus:ring-signal/10 max-sm:w-full" /><button type="submit" disabled={create.isPending || !url.trim()} className="h-[43px] cursor-pointer border border-ink bg-ink px-[18px] text-[13px] font-bold text-paper hover:border-signal hover:bg-signal disabled:cursor-not-allowed disabled:opacity-45 max-sm:mt-2 max-sm:w-full">{create.isPending ? "Starting…" : "Analyze site"}</button></div>
    {create.isError && <p className="mb-0 mt-[9px] text-xs text-flag">{create.error.message}</p>}
  </form>;
}
