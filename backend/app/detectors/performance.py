def compute_performance(soup, html_bytes, asset_bytes, ttfb_ms):
    scripts = soup.find_all("script", src=True)

    return {"ttfb_ms": round(ttfb_ms, 2), "total_page_weight_kb": round((html_bytes + asset_bytes) / 1024, 2), "render_blocking_scripts": sum(1 for tag in scripts if not tag.get("async") and not tag.get("defer") and tag.find_parent("head"))}
