"""Deterministic, public-signal technology detection.

Scores are heuristic evidence scores, not probabilities.  A score combines the
strongest evidence from each source family; repeated matches in one asset do
not increase the score.
"""
from collections import defaultdict
from math import prod
import re
from urllib.parse import urlsplit, urlunsplit

class TechDetector:
    """Collect explainable public technology signals without guessing backends."""

    CATEGORIES = (
        "frontend", "backend", "languages", "server_runtime", "styling",
        "hosting", "tooling", "analytics",
    )

    def __init__(self):
        self._findings = defaultdict(lambda: defaultdict(list))
        self._seen = set()

    @staticmethod
    def _clean_source(source):
        source = str(source or "")
        try:
            parts = urlsplit(source)
            if parts.scheme and parts.netloc:
                return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        except ValueError:
            pass
        return source

    @staticmethod
    def _contains(text, pattern):
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    def _record(self, category, name, source_type, source, signature, explanation, weight, family):
        source = self._clean_source(source)
        key = (category, name, family, signature, source)
        if key in self._seen:
            return
        self._seen.add(key)
        self._findings[category][name].append({
            "source_type": source_type,
            "source": source or "public response",
            "signature": signature,
            "explanation": explanation,
            "weight": weight,
            "family": family,
        })

    def _rules(self, category, source_type, family, rules):
        for name, signature, explanation, weight, matcher in rules:
            if matcher():
                self._record(category, name, source_type, self._source_for(source_type), signature, explanation, weight, family)

    def _source_for(self, source_type):
        return source_type

    def scan_headers(self, headers):
        headers = {str(k).lower(): str(v) for k, v in dict(headers).items()}
        server_rules = [
            ("Nginx", r"\bnginx\b", "Server header names nginx.", .75),
            ("Apache", r"\bapache(?:/|\b)", "Server header names Apache.", .75),
            ("Microsoft IIS", r"\bmicrosoft-iis\b|\biis\b", "Server header names Microsoft IIS.", .75),
            ("Caddy", r"\bcaddy\b", "Server header names Caddy.", .65),
            ("Cloudflare", r"\bcloudflare\b", "Server header names Cloudflare.", .65),
            ("Vercel", r"\bvercel\b", "Server header names Vercel.", .65),
        ]
        for name, signature, explanation, weight in server_rules:
            if self._contains(headers.get("server", ""), signature):
                self._record("hosting", name, "header", "Server", signature, explanation, weight, "header")

        powered = headers.get("x-powered-by", "")
        powered_rules = [
            ("Express.js", r"\bexpress\b", "X-Powered-By names Express.js; this is a framework clue, not proof of the application stack.", .60, "backend"),
            ("Laravel", r"\blaravel\b", "X-Powered-By names Laravel; header clues can be customized or proxied.", .55, "backend"),
            ("Ruby on Rails", r"\b(?:rails|ruby on rails)\b", "X-Powered-By names Ruby on Rails; header clues can be customized or proxied.", .55, "backend"),
            ("ASP.NET", r"\basp\.net\b", "X-Powered-By names ASP.NET; header clues can be customized or proxied.", .55, "backend"),
        ]
        for name, signature, explanation, weight, category in powered_rules:
            if self._contains(powered, signature):
                self._record(category, name, "header", "X-Powered-By", signature, explanation, weight, "header")

        runtime_rules = [
            ("PHP", r"\bphp(?:/|\b)", "X-Powered-By names PHP; this is a server-runtime clue.", .60),
            ("Node.js", r"\bexpress\b|\bnode(?:/|\b)", "X-Powered-By names Node.js or Express; this is a runtime clue, not proof of the application stack.", .55),
            ("C# / .NET", r"\basp\.net\b|\bdotnet\b", "X-Powered-By names ASP.NET or .NET; this is a runtime clue.", .55),
        ]
        for name, signature, explanation, weight in runtime_rules:
            if self._contains(powered, signature):
                self._record("server_runtime", name, "header", "X-Powered-By", signature, explanation, weight, "header")

    def scan_cookies(self, cookies):
        # Cookie values are intentionally ignored: only names are useful signals.
        if hasattr(cookies, "get_dict"):
            names = set(cookies.get_dict())
        elif isinstance(cookies, dict):
            names = set(cookies)
        else:
            names = set(str(cookies).split(";"))
            names = {name.split("=", 1)[0].strip() for name in names if "=" in name}
        rules = [
            ("Cloudflare", "__cf_bm", "A Cloudflare bot-management cookie name was returned.", .55, "hosting"),
            ("Django", "csrftoken", "A Django CSRF cookie name was returned; this is a server-framework clue.", .55, "backend"),
            ("Laravel", "laravel_session", "A Laravel session cookie name was returned; this is a server-framework clue.", .55, "backend"),
            ("WordPress", "wordpress_logged_in", "A WordPress login cookie name was returned; this is a server-framework clue.", .55, "backend"),
        ]
        for name, cookie, explanation, weight, category in rules:
            if cookie in {item.lower() for item in names}:
                self._record(category, name, "cookie", "Cookie name", cookie, explanation, weight, "cookie")

    def scan_html(self, html, source="HTML"):
        rules = [
            ("React", r"\bdata-reactroot\b", "React-specific data-reactroot marker found in returned HTML.", .78, "frontend"),
            ("Next.js", r"\b__next_data__\b", "Next.js __NEXT_DATA__ page marker found in returned HTML.", .75, "frontend"),
            ("Vue.js", r"\bdata-v-app\b", "Vue-specific data-v-app marker found in returned HTML.", .75, "frontend"),
            ("Angular", r"\bng-version\s*=|['\"]ng-version['\"]", "Angular ng-version marker found in returned HTML.", .78, "frontend"),
            ("Svelte", r"\bdata-svelte\b", "Svelte-specific data-svelte marker found in returned HTML.", .65, "frontend"),
            ("WordPress", r"\bwp-(?:content|json)\b", "WordPress-specific wp-content or wp-json marker found in returned HTML.", .70, "backend"),
            ("Django", r"\bcsrfmiddlewaretoken\b", "Django CSRF form-token marker found in returned HTML.", .55, "backend"),
            ("Ruby on Rails", r"\bdata-turbo(?:-permanent)?(?:=|\b)", "Rails-specific data-turbo marker found in returned HTML.", .50, "backend"),
        ]
        for name, signature, explanation, weight, category in rules:
            if self._contains(html, signature):
                self._record(category, name, "html", source, signature, explanation, weight, "page")

    def scan_script_url(self, source):
        path = self._clean_source(source).lower()
        rules = [
            ("Next.js", r"(?:^|/)_next/", "Script URL is under a distinctive /_next/ asset path.", .70, "frontend"),
            ("WordPress", r"(?:^|/)wp-content/", "Script URL is under a distinctive /wp-content/ asset path.", .60, "backend"),
            ("Tailwind CSS", r"(?:^|/)tailwindcss/", "Asset URL references a distinctive tailwindcss path.", .65, "styling"),
            ("Bootstrap", r"(?:^|/)bootstrap(?:\.|/)", "Asset URL references a distinctive Bootstrap path.", .55, "styling"),
            ("Vite", r"(?:^|/)@vite/client(?:\?|$)", "Asset URL references the distinctive Vite client module.", .70, "tooling"),
        ]
        for name, signature, explanation, weight, category in rules:
            if self._contains(path, signature):
                self._record(category, name, "script_url", source, signature, explanation, weight, "asset")

    def scan_js_bundle(self, content, source=""):
        # These are distinctive runtime/library markers, not bare technology names.
        rules = [
            ("React", r"__REACT_DEVTOOLS_GLOBAL_HOOK__|react-dom|react__", "React-specific runtime marker found in script content.", .70, "frontend"),
            ("Vue.js", r"__VUE__|createApp\s*\(", "Vue-specific runtime marker found in script content.", .65, "frontend"),
            ("Svelte", r"svelte/internal|__svelte", "Svelte-specific runtime marker found in script content.", .70, "frontend"),
            ("jQuery", r"jquery\.fn\.jquery|jquery\.min\.js", "jQuery-specific runtime marker found in script content.", .70, "frontend"),
            ("Webpack", r"webpackChunk|__webpack_require__", "Webpack-specific runtime marker found in script content.", .65, "tooling"),
            ("Vite", r"__vite__|@vite/client", "Vite-specific runtime marker found in script content.", .65, "tooling"),
        ]
        for name, signature, explanation, weight, category in rules:
            if self._contains(content, signature):
                self._record(category, name, "script_content", source, signature, explanation, weight, "asset")

    def scan_server_languages(self, headers):
        # Kept as a compatibility entry point. Server runtimes are now reported
        # from explicit response headers by scan_headers and never from bundles.
        self.scan_headers(headers)

    def scan_languages(self, content, source="", url=""):
        # Delivered JavaScript is observable; original TypeScript is not.
        # Never claim TypeScript from a .js asset or an inline script.
        if self._clean_source(url).lower().split("?", 1)[0].endswith((".js", ".mjs", ".cjs")):
            self._record("languages", "JavaScript", "asset_url", url, ".js asset", "A JavaScript asset was delivered to the browser; this does not reveal the original source language.", .55, "asset")

    def scan_css(self, content, source=""):
        rules = [
            ("Tailwind CSS", r"(?:--tw-|\btailwindcss\b)", "Tailwind-specific CSS custom properties or runtime marker found in stylesheet content.", .70),
            ("Bootstrap", r"(?:data-bs-|--bs-)", "Bootstrap-specific CSS custom properties or component marker found in stylesheet content.", .60),
            ("styled-components", r"data-styled(?:-components)?", "styled-components runtime marker found in stylesheet content.", .65),
        ]
        for name, signature, explanation, weight in rules:
            if self._contains(content, signature):
                self._record("styling", name, "css", source, signature, explanation, weight, "css")

    def scan_rendered_signals(self, signals):
        text = " ".join(map(str, signals if isinstance(signals, (list, tuple)) else [signals]))
        # Rendered browser signals remain frontend/tooling only.
        rules = [
            ("Vite", r"__vite__|@vite/client", "Vite-specific runtime marker found in the rendered browser DOM.", .65, "tooling"),
            ("Webpack", r"webpackChunk|__webpack_require__", "Webpack-specific runtime marker found in the rendered browser DOM.", .60, "tooling"),
        ]
        for name, signature, explanation, weight, category in rules:
            if self._contains(text, signature):
                self._record(category, name, "rendered_dom", "Rendered browser DOM", signature, explanation, weight, "page")

    @staticmethod
    def _confidence(score):
        return "high" if score >= .75 else "medium" if score >= .45 else "low"

    def _score(self, evidence):
        # Each source family contributes its strongest clue only. This makes
        # duplicate matches in one bundle harmless while allowing independent
        # HTML/header/cookie evidence to corroborate a finding.
        strongest = {}
        for item in evidence:
            family = item["family"]
            strongest[family] = max(strongest.get(family, 0), item["weight"])
        return round(min(1.0, 1 - prod(1 - value for value in strongest.values())), 2)

    def results(self):
        output = {}
        for category in self.CATEGORIES:
            findings = []
            for name, evidence in self._findings.get(category, {}).items():
                score = self._score(evidence)
                confidence = self._confidence(score)
                public_evidence = [f"{item['explanation']} Source: {item['source']}" for item in evidence]
                findings.append({
                    "name": name,
                    "confidence": confidence,
                    "score": score,
                    "evidence": public_evidence,
                    "evidence_items": evidence,
                })
            output[category] = sorted(findings, key=lambda item: (-item["score"], item["name"]))
        return output
