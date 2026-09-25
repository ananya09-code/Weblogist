from app.detectors.tech_detector import TechDetector


def test_confidence_labels_use_documented_thresholds():
    assert TechDetector._confidence(0.75) == "high"
    assert TechDetector._confidence(0.45) == "medium"
    assert TechDetector._confidence(0.44) == "low"


def finding(detector, category, name):
    return next(item for item in detector.results()[category] if item["name"] == name)


def test_specific_frontend_signatures_and_structured_evidence():
    detector = TechDetector()
    detector.scan_html('<div data-reactroot></div>')
    detector.scan_js_bundle("__REACT_DEVTOOLS_GLOBAL_HOOK__", "https://example.test/assets/app.js?secret=1")

    item = finding(detector, "frontend", "React")
    assert item["score"] >= 0.75
    assert item["confidence"] == "high"
    assert item["evidence_items"][0]["source_type"] == "html"
    assert "secret=1" not in item["evidence_items"][1]["source"]
    assert item["evidence_items"][1]["source"] == "https://example.test/assets/app.js"


def test_duplicate_markers_in_one_asset_do_not_inflate_score():
    detector = TechDetector()
    detector.scan_js_bundle("react-dom react-dom react-dom", "https://example.test/app.js")
    detector.scan_js_bundle("react-dom", "https://example.test/app.js")

    item = finding(detector, "frontend", "React")
    assert item["score"] == 0.7
    assert len(item["evidence_items"]) == 1


def test_distinct_source_families_corroborate():
    single = TechDetector()
    single.scan_html('<div data-reactroot></div>')
    corroborated = TechDetector()
    corroborated.scan_html('<div data-reactroot></div>')
    corroborated.scan_js_bundle("__REACT_DEVTOOLS_GLOBAL_HOOK__", "https://example.test/app.js")

    assert finding(corroborated, "frontend", "React")["score"] > finding(single, "frontend", "React")["score"]


def test_generic_backend_names_in_frontend_bundle_are_not_backend_findings():
    detector = TechDetector()
    detector.scan_js_bundle("const text = 'Django Laravel Rails';", "https://example.test/app.js")

    assert detector.results()["backend"] == []


def test_javascript_delivery_does_not_claim_typescript_source():
    detector = TechDetector()
    detector.scan_languages("var x = 1", "https://example.test/app.js?cache=1", "https://example.test/app.js")

    assert finding(detector, "languages", "JavaScript")["score"] == 0.55
    assert not any(item["name"] == "TypeScript" for item in detector.results()["languages"])


def test_server_header_is_infrastructure_not_application_framework():
    detector = TechDetector()
    detector.scan_headers({"Server": "nginx/1.25"})

    assert finding(detector, "hosting", "Nginx")["evidence_items"][0]["source_type"] == "header"
    assert detector.results()["backend"] == []


def test_cookie_names_are_evidence_without_values():
    detector = TechDetector()
    detector.scan_cookies({"laravel_session": "secret-session-value"})

    item = finding(detector, "backend", "Laravel")
    assert item["evidence_items"][0]["source"] == "Cookie name"
    assert "secret-session-value" not in str(item)


def test_scores_stay_bounded_and_old_evidence_remains_available():
    detector = TechDetector()
    detector.scan_html('<div data-reactroot></div>')
    detector.scan_js_bundle("__REACT_DEVTOOLS_GLOBAL_HOOK__", "https://example.test/app.js")

    item = finding(detector, "frontend", "React")
    assert 0 <= item["score"] <= 1
    assert isinstance(item["evidence"], list)
    assert all(isinstance(value, str) for value in item["evidence"])
