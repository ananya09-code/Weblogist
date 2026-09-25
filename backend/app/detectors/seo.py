import json
from bs4 import BeautifulSoup


def extract_seo(soup, robots_status="unknown"):
    title = soup.title.get_text(strip=True) if soup.title else None
    description = soup.find(
        "meta", attrs={"name": lambda x: x and x.lower() == "description"})
    canonical = soup.find("link", rel=lambda x: x and "canonical" in x)
    og = {tag["property"][3:]: tag.get("content") for tag in soup.find_all("meta", attrs={
        "property": lambda x: x and x.lower().startswith("og:")}) if tag.get("property") and tag.get("content")}
    structured = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            structured.append(json.loads(tag.string or "{}"))
        except (ValueError, TypeError):
            structured.append(None)
    return {"title": title, "meta_description": description.get("content") if description else None, "og": og, "canonical": canonical.get("href") if canonical else None, "robots_status": robots_status, "structured_data": structured}
