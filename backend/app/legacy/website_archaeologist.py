#!/usr/bin/env python3
"""
Website Archaeologist
----------------------
Enter a URL, get back its tech stack, page structure, and likely API endpoints.

Usage:
    python website_archaeologist.py https://example.com

Install deps:
    pip install requests beautifulsoup4
"""

import re
import sys
import json
import urllib.parse as urlparse
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (WebsiteArchaeologist/1.0)"}
TIMEOUT = 10

# --- Signature database: (label, where to look, pattern) -------------------
TECH_SIGNATURES = {
    "headers": {
        "server": {
            "nginx": "Nginx", "apache": "Apache", "cloudflare": "Cloudflare",
            "vercel": "Vercel", "awselb": "AWS (ELB)", "gws": "Google Web Server",
        },
        "x-powered-by": {
            "express": "Express.js", "php": "PHP", "asp.net": "ASP.NET",
            "next.js": "Next.js",
        },
    },
    "meta_generator": {
        "wordpress": "WordPress", "shopify": "Shopify", "wix": "Wix",
        "squarespace": "Squarespace", "drupal": "Drupal", "webflow": "Webflow",
        "hugo": "Hugo", "gatsby": "Gatsby",
    },
    "html_markers": {
        "__next": "Next.js", "/_next/static": "Next.js", "__NEXT_DATA__": "Next.js",
        "data-reactroot": "React", "ng-version": "Angular",
        "__nuxt": "Nuxt.js", "data-svelte": "Svelte", "wp-content": "WordPress",
        "cdn.shopify.com": "Shopify", "static.wixstatic.com": "Wix",
        "webflow.js": "Webflow", "__vite": "Vite", "astro-island": "Astro",
        "data-remix": "Remix",
    },
    "script_src": {
        "react": "React", "vue": "Vue.js", "jquery": "jQuery",
        "bootstrap": "Bootstrap", "tailwind": "Tailwind CSS",
        "gtag/js": "Google Analytics", "googletagmanager": "Google Tag Manager",
        "segment.com": "Segment", "intercom": "Intercom", "stripe.com/v3": "Stripe.js",
        "sentry": "Sentry", "hotjar": "Hotjar",
    },
}

API_HINT_PATTERN = re.compile(
    r"""["'`](/api/[a-zA-Z0-9_\-/{}.]*|https?://[a-zA-Z0-9.\-]+/api/[a-zA-Z0-9_\-/{}.]*)["'`]"""
)
FETCH_CALL_PATTERN = re.compile(
    r"""(fetch|axios\.\w+|\$\.ajax)\s*\(\s*["'`]([^"'`]+)["'`]""")


def fetch(url, session):
    resp = session.get(url, headers=HEADERS,
                       timeout=TIMEOUT, allow_redirects=True)
    return resp


def detect_from_headers(headers, findings):
    for key, table in TECH_SIGNATURES["headers"].items():
        val = headers.get(key, "").lower()
        for needle, label in table.items():
            if needle in val:
                findings.add(label)


def detect_from_html(html, findings, script_urls):
    lower = html.lower()
    for needle, label in TECH_SIGNATURES["html_markers"].items():
        if needle.lower() in lower:
            findings.add(label)

    soup = BeautifulSoup(html, "html.parser")

    gen = soup.find("meta", attrs={"name": "generator"})
    if gen and gen.get("content"):
        content = gen["content"].lower()
        for needle, label in TECH_SIGNATURES["meta_generator"].items():
            if needle in content:
                findings.add(label)

    for script in soup.find_all("script", src=True):
        src = script["src"]
        script_urls.append(src)
        for needle, label in TECH_SIGNATURES["script_src"].items():
            if needle in src.lower():
                findings.add(label)

    for script in soup.find_all("script", src=False):
        if script.string:
            for needle, label in TECH_SIGNATURES["script_src"].items():
                if needle in script.string.lower():
                    findings.add(label)

    return soup


def crawl_links(soup, base_url, same_domain_only=True):
    base = urlparse.urlparse(base_url)
    links = set()
    for a in soup.find_all("a", href=True):
        href = urlparse.urljoin(base_url, a["href"])
        parsed = urlparse.urlparse(href)
        if parsed.scheme not in ("http", "https"):
            continue
        if same_domain_only and parsed.netloc != base.netloc:
            continue
        clean = parsed._replace(fragment="").geturl()
        links.add(clean)
    return links


def check_well_known(base_url, session):
    found = {}
    for path in ("/sitemap.xml", "/robots.txt", "/.well-known/security.txt"):
        try:
            r = session.get(urlparse.urljoin(base_url, path),
                            headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200 and len(r.text.strip()) > 0:
                found[path] = r.text[:2000]
        except requests.RequestException:
            pass
    return found


FRAMEWORK_CONTENT_SIGNATURES = {
    "react": "React", "useState": "React", "reactDOM": "React",
    "__vue__": "Vue.js", "vueComponent": "Vue.js",
    "ng-version": "Angular", "@angular/core": "Angular",
    "svelte-": "Svelte",
    "next/dist": "Next.js", "next/router": "Next.js",
}


def scan_js_for_apis(script_urls, base_url, session, findings, max_files=8):
    """Scans same-origin JS bundles for both API path patterns and
    framework fingerprints hidden inside the (often hashed) chunk content."""
    api_hints = set()
    checked = 0
    for src in script_urls:
        if checked >= max_files:
            break
        full = urlparse.urljoin(base_url, src)
        if urlparse.urlparse(full).netloc != urlparse.urlparse(base_url).netloc:
            continue  # skip third-party scripts (analytics, CDNs, etc.)
        try:
            r = session.get(full, headers=HEADERS, timeout=TIMEOUT)
            checked += 1
            if r.status_code != 200:
                continue
            for m in API_HINT_PATTERN.finditer(r.text):
                api_hints.add(m.group(1))
            for m in FETCH_CALL_PATTERN.finditer(r.text):
                api_hints.add(m.group(2))
            for needle, label in FRAMEWORK_CONTENT_SIGNATURES.items():
                if needle in r.text:
                    findings.add(label)
        except requests.RequestException:
            continue
    return api_hints


def analyze(url, crawl_depth_pages=15):
    session = requests.Session()
    report = {"url": url, "tech_stack": [], "pages": [], "well_known_files": [],
              "api_endpoints_found": [], "notes": []}

    try:
        resp = fetch(url, session)
    except requests.RequestException as e:
        report["notes"].append(f"Failed to fetch {url}: {e}")
        return report

    findings = set()
    detect_from_headers(resp.headers, findings)

    script_urls = []
    soup = detect_from_html(resp.text, findings, script_urls)

    # Crawl a handful of internal pages
    links = crawl_links(soup, url)
    report["pages"] = sorted(links)[:crawl_depth_pages]

    # Well-known files
    wk = check_well_known(url, session)
    report["well_known_files"] = list(wk.keys())
    if "/sitemap.xml" in wk:
        report["notes"].append(
            "sitemap.xml found — parse it for a fuller page list.")

    # API hints + deeper framework fingerprints from same-origin JS bundles
    apis = scan_js_for_apis(script_urls, url, session, findings)
    report["api_endpoints_found"] = sorted(apis)
    if not apis:
        report["notes"].append(
            "No API paths found in static JS. Site may be server-rendered, "
            "or APIs are only called after JS execution — would need a headless "
            "browser (Playwright) to catch those via network interception."
        )

    if not links:
        report["notes"].append(
            "No internal links found in raw HTML — this is a strong sign of a "
            "client-rendered SPA (React/Vue/etc. mounting into an empty div). "
            "The crawler needs Playwright to see the page after hydration."
        )

    report["tech_stack"] = sorted(findings) or [
        "No strong signals detected — may be a heavily custom or obfuscated stack"]
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python website_archaeologist.py <url>")
        sys.exit(1)

    target = sys.argv[1]
    if not target.startswith("http"):
        target = "https://" + target

    print(f"Digging into {target} ...\n")
    result = analyze(target)
    print(json.dumps(result, indent=2))
