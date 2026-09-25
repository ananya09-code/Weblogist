"""Evidence-based technology detector used by the scan pipeline."""
from collections import defaultdict


class TechDetector:
    def __init__(self):
        self._findings = defaultdict(dict)

    def _add(self, category, name, confidence, evidence):
        score = {"low": .35, "medium": .65, "high": .95}[confidence]
        old = self._findings[category].get(name)
        if old and old["score"] >= score:
            return
        self._findings[category][name] = {
            "name": name, "confidence": confidence, "score": score, "evidence": [evidence]}

    def scan_headers(self, headers):
        headers = {k.lower(): v for k, v in dict(headers).items()}
        for header, entries in {"server": {"nginx": "Nginx", "cloudflare": "Cloudflare", "vercel": "Vercel", "apache": "Apache", "twisted": "Twisted"}, "x-powered-by": {"php": "PHP", "express": "Express.js", "asp.net": "ASP.NET", "laravel": "Laravel", "rails": "Ruby on Rails"}}.items():
            value = str(headers.get(header, "")).lower()
            for needle, name in entries.items():
                if needle in value:
                    self._add("hosting" if header == "server" else "backend",
                              name, "high", f"{header}: {headers[header]}")

    def scan_cookies(self, cookies):
        text = str(cookies).lower()
        for needle, name, category in [("__cf_bm", "Cloudflare", "hosting"), ("_ga", "Google Analytics", "analytics"), ("csrfmiddlewaretoken", "Django", "backend")]:
            if needle in text:
                self._add(category, name, "medium", f"cookie: {needle}")

    def scan_html(self, html):
        lower = html.lower()
        for needle, name, category, confidence in [("data-reactroot", "React", "frontend", "high"), ("react", "React", "frontend", "medium"), ("vue", "Vue.js", "frontend", "high"), ("ng-version", "Angular", "frontend", "high"), ("__next", "Next.js", "frontend", "high"), ("svelte", "Svelte", "frontend", "high"), ("wp-content", "WordPress", "backend", "high"), ("wp-json", "WordPress", "backend", "high"), ("laravel_session", "Laravel", "backend", "high"), ("csrfmiddlewaretoken", "Django", "backend", "high"), ("rails-ujs", "Ruby on Rails", "backend", "high"), ("__twilio", "Twilio", "backend", "high"), ("twilio.com", "Twilio", "backend", "high"), ("twisted.web", "Twisted", "backend", "high"), ("supabase.co", "Supabase", "backend", "medium"), ("firebaseio.com", "Firebase", "backend", "medium"), ("generator", "CMS", "backend", "low"), ("tailwind", "Tailwind CSS", "styling", "high")]:
            if needle in lower:
                self._add(category, name, confidence, f"HTML marker: {needle}")

    def scan_js_bundle(self, content, source=""):
        for needle, name, category, confidence in [("usestate", "React", "frontend", "high"), ("reactdom", "React", "frontend", "high"), ("vue", "Vue.js", "frontend", "high"), ("@angular/core", "Angular", "frontend", "high"), ("svelte", "Svelte", "frontend", "high"), ("next/router", "Next.js", "frontend", "high"), ("jquery", "jQuery", "frontend", "high"), ("twilio", "Twilio", "backend", "high"), ("twisted.web", "Twisted", "backend", "high"), ("laravel", "Laravel", "backend", "high"), ("django", "Django", "backend", "medium"), ("rails-ujs", "Ruby on Rails", "backend", "high"), ("supabase.co", "Supabase", "backend", "high"), ("firebase", "Firebase", "backend", "medium")]:
            if needle in content.lower():
                self._add(category, name, confidence, f"{source}: {needle}")

    def scan_server_languages(self, headers):
        headers = {key.lower(): str(value).lower()
                   for key, value in dict(headers).items()}
        direct = [("php", "PHP", "x-powered-by"), ("express", "Node.js", "x-powered-by"), ("asp.net", "C# / ASP.NET", "x-powered-by"),
                  ("dotnet", "C# / ASP.NET", "x-powered-by"), ("python", "Python", "server"), ("ruby", "Ruby", "server")]
        for needle, language, header in direct:
            value = headers.get(header, "")
            if needle in value:
                self._add("languages", language, "high",
                          f"{header}: {headers[header]}")

    def scan_languages(self, content, source="", url=""):
        """Only claim languages that have direct, low-false-positive evidence.

        A browser cannot reliably reveal a site's server-side implementation
        (a Python API can serve a React bundle), so backend framework signals
        stay in the backend cluster. Here we report client languages from file
        extensions and strong compiler/runtime markers only.
        """
        text = content.lower()
        source_url = url.lower()
        if source_url.endswith((".js", ".mjs", ".cjs")):
            self._add("languages", "JavaScript", "medium", f"{
                      source}: JavaScript bundle extension")
        if source_url.endswith((".ts", ".tsx", ".mts", ".cts")):
            self._add("languages", "TypeScript", "high", f"{
                      source}: TypeScript source extension")
        strong_markers = [("__awaiter", "TypeScript", "generated async helper"), ("__generator", "TypeScript",
                                                                                  "generated generator helper"), ("sourcemappingurl", "JavaScript", "JavaScript source map")]
        for marker, language, evidence in strong_markers:
            if marker in text:
                self._add("languages", language, "medium",
                          f"{source}: {evidence}")

    def scan_css(self, content, source=""):
        for needle, name in [("tailwind", "Tailwind CSS"), ("bootstrap", "Bootstrap"), ("foundation", "Foundation"), ("bulma", "Bulma"), ("chakra", "Chakra UI"), ("emotion", "Emotion"), ("styled-components", "styled-components"), (".scss", "Sass")]:
            if needle in content.lower():
                self._add("styling", name, "high", f"{source}: {needle}")

    def scan_rendered_signals(self, signals):
        text = " ".join(map(str, signals if isinstance(
            signals, (list, tuple)) else [signals]))
        self.scan_html(text)
        for needle, name in [("webpack", "Webpack"), ("vite", "Vite")]:
            if needle in text.lower():
                self._add("tooling", name, "high", f"window: {needle}")

    def results(self):
        categories = ("frontend", "backend", "styling", "hosting",
                      "tooling", "analytics", "languages")
        return {category: sorted(self._findings.get(category, {}).values(), key=lambda item: (-item["score"], item["name"])) for category in categories}
