import { useId, useState } from "react";
import { useCreateScan } from "../lib/api";
import { useNavigate } from "@tanstack/react-router";

export function UrlInputBar() {
  const [url, setUrl] = useState("");
  const inputId = useId();
  const create = useCreateScan();
  const navigate = useNavigate();
  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!url.trim() || create.isPending) return;
    create.mutate(url.trim(), { onSuccess: (scan) => navigate({ to: "/scans/$id", params: { id: scan.scan_id } }) });
  }
  return <form className="url-form" onSubmit={submit}><label htmlFor={inputId}>Enter a site to inspect</label><div className="url-row"><input id={inputId} className="url-input" type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com" required /><button className="pixel-button" type="submit" disabled={create.isPending || !url.trim()}>{create.isPending ? "OPENING SITE…" : "INSPECT SITE"}</button></div>{create.isError && <p className="form-error">{create.error.message}</p>}</form>;
}
