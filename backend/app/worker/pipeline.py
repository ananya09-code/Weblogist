"""Static analysis pipeline. Playwright is conditional and optional."""
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from ..detectors.tech_detector import TechDetector
from ..detectors.seo import extract_seo
from ..detectors.performance import compute_performance
from ..legacy.website_archaeologist import crawl_links, API_HINT_PATTERN, FETCH_CALL_PATTERN
from .security import fetch, validate_url


def _routes(text, base):
    values = set()
    for pattern in (API_HINT_PATTERN, FETCH_CALL_PATTERN):
        values.update(m.group(1) for m in pattern.finditer(text))
    output = {}
    for value in values:
        if value.startswith("http") and urlparse(value).hostname != urlparse(base).hostname:
            continue
        path = value.split("?", 1)[0] if not value.startswith(
            "http") else urlparse(value).path
        if path.startswith(("/api/", "/graphql")):
            output[path] = {"path": path,
                            "source_file": None, "method_guess": "GET"}
    return list(output.values())


def run_pipeline(url):
    url = validate_url(url)
    response, final_url, ttfb = fetch(url)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    detector = TechDetector()
    detector.scan_headers(response.headers)
    detector.scan_cookies(response.cookies)
    detector.scan_html(html)
    detector.scan_server_languages(response.headers)
    detector.scan_languages(html, "HTML", final_url)
    detector.scan_css("\n".join(tag.get_text()
                      for tag in soup.find_all("style")), "inline CSS")
    scripts = [urljoin(final_url, tag["src"])
               for tag in soup.find_all("script", src=True)]
    stylesheets = [urljoin(final_url, tag["href"]) for tag in soup.find_all(
        "link", href=True) if "stylesheet" in (tag.get("rel") or [])]
    same_origin = [src for src in scripts if urlparse(
        src).hostname == urlparse(final_url).hostname][:8]
    routes = _routes(html, final_url)
    asset_bytes = 0
    for stylesheet in stylesheets:
        if urlparse(stylesheet).hostname != urlparse(final_url).hostname:
            continue
        try:
            css_response, _, _ = fetch(stylesheet)
            css_text = css_response.text
            asset_bytes += len(css_response.content)
            detector.scan_css(css_text, stylesheet)
        except Exception:
            pass
    for script in same_origin:
        try:
            bundle_response, _, _ = fetch(script)
            content = bundle_response.content
            asset_bytes += len(content)
            text = content.decode("utf-8", "ignore")
            routes.extend(_routes(text, final_url))
            detector.scan_js_bundle(text, script)
            detector.scan_languages(text, script, script)
        except Exception:
            pass
    links = crawl_links(soup, final_url)
    frontend = detector.results().get("frontend", [])
    # A linkless shell is the strongest SPA signal. Also render when the shell
    # exposes a generic title even if a bundle already contains a framework hint;
    # the static title is commonly the Vite placeholder rather than the real title.
    needs_playwright = not links and (not any(item["score"] > .6 for item in frontend) or (
        soup.title and soup.title.get_text(strip=True).lower() in {"web", "app", "react app"}))
    if needs_playwright:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(final_url, wait_until="networkidle", timeout=15000)
                detector.scan_rendered_signals(
                    page.evaluate("Object.keys(window)"))
                rendered = BeautifulSoup(page.content(), "html.parser")
                links = crawl_links(rendered, final_url)
                soup = rendered
                browser.close()
        except Exception:
            pass
    robots_status = "unknown"
    try:
        robots, _, _ = fetch(urljoin(final_url, "/robots.txt"))
        robots_status = "allowed" if robots.is_success else "blocked_or_missing"
    except Exception:
        robots_status = "unavailable"
    tech_stack = detector.results()
    if not tech_stack.get("backend"):
        tech_stack["backend"] = [{"name": "Unable to determine", "confidence": "low", "score": 0.0, "evidence": [
            "No backend signal cleared the confidence threshold"]}]
    return {"tech_stack": tech_stack, "api_routes": list({item["path"]: item for item in routes}.values()), "seo": extract_seo(soup, robots_status), "performance": compute_performance(soup, len(response.content), asset_bytes, ttfb), "raw_headers": dict(response.headers), "pages": sorted(links)[:15], "needs_playwright": needs_playwright}
