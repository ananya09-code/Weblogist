"""Bounded, SSRF-safe static website analysis."""
from __future__ import annotations

import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .security import MAX_REDIRECTS, UnsafeURLError, normalize_url, resolve_and_validate, validate_url

USER_AGENT = "WebsiteArchaeologistBot/1.0 (+https://example.com/bot)"
TIMEOUT = (5, 15)
MAX_BODY = 10 * 1024 * 1024
MAX_SCRIPTS = 10

TECH_SIGNATURES = {
    "server": {"nginx": "Nginx", "apache": "Apache", "cloudflare": "Cloudflare", "vercel": "Vercel", "awselb": "AWS (ELB)"},
    "x-powered-by": {"express": "Express.js", "php": "PHP", "asp.net": "ASP.NET", "next.js": "Next.js"},
}
META_SIGNATURES = {"wordpress": "WordPress", "shopify": "Shopify", "wix": "Wix", "squarespace": "Squarespace", "drupal": "Drupal", "webflow": "Webflow", "hugo": "Hugo", "gatsby": "Gatsby"}
HTML_SIGNATURES = {"__next": "Next.js", "/_next/static": "Next.js", "__NEXT_DATA__": "Next.js", "data-reactroot": "React", "ng-version": "Angular", "__nuxt": "Nuxt.js", "data-svelte": "Svelte", "wp-content": "WordPress", "cdn.shopify.com": "Shopify", "webflow.js": "Webflow", "__vite": "Vite", "astro-island": "Astro"}
SCRIPT_SIGNATURES = {"react": "React", "vue": "Vue.js", "jquery": "jQuery", "bootstrap": "Bootstrap", "tailwind": "Tailwind CSS", "gtag/js": "Google Analytics", "googletagmanager": "Google Tag Manager", "segment.com": "Segment", "intercom": "Intercom", "stripe.com/v3": "Stripe.js", "sentry": "Sentry", "hotjar": "Hotjar"}
API_PATTERN = re.compile(r"""["'`](/(?:api|graphql)(?:/[a-zA-Z0-9_.~%/{}$-]*)?|https?://[^\s"'`]+)["'`]""")
FETCH_PATTERN = re.compile(r"""(?:fetch|axios\.\w+|\$\.ajax)\s*\(\s*["'`]([^"'`\s]+)["'`]""")


def _safe_get(url: str) -> requests.Response:
    """GET with redirect revalidation and a hard body cap."""
    current = validate_url(url)
    for _ in range(MAX_REDIRECTS + 1):
        response = requests.get(current, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/javascript,text/plain;q=0.8,*/*;q=0.1"}, timeout=TIMEOUT, allow_redirects=False, stream=True)
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise UnsafeURLError("Redirect has no location")
            current = validate_url(urljoin(current, location))
            continue
        content = b"".join(response.iter_content(64 * 1024))
        if len(content) > MAX_BODY:
            response.close()
            raise ValueError("Response body exceeds the 10MB limit")
        response._content = content
        response._content_consumed = True
        return response
    raise UnsafeURLError("Too many redirects")


def _is_same_host(url: str, base: str) -> bool:
    return urlparse(url).hostname == urlparse(base).hostname and urlparse(url).port == urlparse(base).port


def _tech(headers: requests.structures.CaseInsensitiveDict[str], html: str, scripts: list[str], inline: str) -> list[dict[str, Any]]:
    found: dict[str, str] = {}
    for header, signatures in TECH_SIGNATURES.items():
        value = headers.get(header, "").lower()
        for needle, name in signatures.items():
            if needle in value: found[name] = "high"
    low = html.lower()
    for needle, name in HTML_SIGNATURES.items():
        if needle in low: found[name] = "high"
    generator = BeautifulSoup(html, "html.parser").find("meta", attrs={"name": re.compile("generator", re.I)})
    if generator and generator.get("content"):
        value = generator["content"].lower()
        for needle, name in META_SIGNATURES.items():
            if needle in value: found[name] = "high"
    for src in scripts + [inline]:
        for needle, name in SCRIPT_SIGNATURES.items():
            if needle in src.lower(): found[name] = "medium"
    return [{"name": name, "category": "detected", "confidence": confidence} for name, confidence in sorted(found.items())]


def _extract_api_hints(content: str, base: str) -> list[dict[str, Any]]:
    values = {m.group(1) for pattern in (API_PATTERN, FETCH_PATTERN) for m in pattern.finditer(content)}
    routes = []
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme in ("http", "https") and not _is_same_host(value, base):
            continue
        path = parsed.path if parsed.scheme else value.split("?", 1)[0]
        if path.startswith("/") and any(part in path for part in ("/api", "/graphql")):
            routes.append({"path": path, "source_file": None, "method_guess": "GET"})
    return routes[:50]


def analyze(url: str) -> dict[str, Any]:
    started = time.perf_counter()
    normalized = validate_url(url)
    response = _safe_get(normalized)
    response.raise_for_status()
    final_url = response.url
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    script_urls = [urljoin(final_url, tag["src"]) for tag in soup.find_all("script", src=True)]
    inline = "\n".join(tag.get_text() for tag in soup.find_all("script") if not tag.get("src"))
    base_path = urlparse(final_url)
    scripts = [src for src in script_urls if _is_same_host(src, final_url)][:MAX_SCRIPTS]
    api_routes = _extract_api_hints(html + "\n" + inline, final_url)
    transferred = len(response.content)
    for script in scripts:
        try:
            script_response = _safe_get(script)
            if script_response.ok:
                content = script_response.content
                transferred += len(content)
                api_routes.extend(_extract_api_hints(content.decode("utf-8", "ignore"), final_url))
        except (requests.RequestException, UnsafeURLError, ValueError):
            continue
    unique_routes = {item["path"]: item for item in api_routes}
    robots_url = urljoin(final_url, "/robots.txt")
    robots_status = "unknown"
    try:
        robots_status = "allowed" if _safe_get(robots_url).ok else "blocked_or_missing"
    except (requests.RequestException, UnsafeURLError, ValueError):
        robots_status = "unavailable"
    title = soup.title.get_text(strip=True) if soup.title else None
    description = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    og = {f"og:{tag.get('property')[3:]}": tag.get("content") for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}) if tag.get("property") and tag.get("content")}
    structured = [tag.get("type") for tag in soup.find_all("script", type="application/ld+json")]
    return {
        "tech_stack": _tech(response.headers, html, script_urls, inline),
        "api_routes": list(unique_routes.values()),
        "seo": {"title": title, "meta_description": description.get("content") if description else None, "og": og, "canonical": canonical.get("href") if canonical else None, "robots_status": robots_status, "structured_data": structured},
        "performance": {"ttfb_ms": round((time.perf_counter() - started) * 1000, 1), "total_page_weight_kb": round(transferred / 1024, 1), "render_blocking_scripts": len([tag for tag in soup.find_all("script", src=True) if not tag.get("defer") and not tag.get("async")])},
        "raw_headers": dict(response.headers),
    }


_CACHE: OrderedDict[str, tuple[datetime, dict[str, Any]]] = OrderedDict()
_CACHE_TTL = timedelta(hours=6)

def cached_analyze(url: str) -> tuple[str, dict[str, Any] | None]:
    normalized = normalize_url(url)
    item = _CACHE.get(normalized)
    if item and datetime.now(timezone.utc) - item[0] < _CACHE_TTL:
        _CACHE.move_to_end(normalized)
        return normalized, item[1]
    result = analyze(normalized)
    _CACHE[normalized] = (datetime.now(timezone.utc), result)
    while len(_CACHE) > 100: _CACHE.popitem(last=False)
    return normalized, result
