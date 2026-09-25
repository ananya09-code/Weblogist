"""SSRF-safe URL normalization and bounded HTTP fetching."""
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse, urlunparse
import httpx
from ..config import get_settings


class UnsafeURLError(ValueError):
    pass


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise UnsafeURLError("URL cannot be empty")
    if "://" not in value:
        value = "https://" + value
    p = urlparse(value)
    if p.scheme.lower() not in {"http", "https"}:
        raise UnsafeURLError("Only http and https URLs are supported")
    if not p.hostname or p.username or p.password:
        raise UnsafeURLError("A valid public HTTP(S) URL is required")
    try:
        port = p.port
    except ValueError as exc:
        raise UnsafeURLError("Invalid URL port") from exc
    host = p.hostname.encode("idna").decode()
    netloc = f"[{host}]" if ":" in host else host
    if port:
        netloc += f":{port}"
    return urlunparse((p.scheme.lower(), netloc, p.path or "/", p.params, p.query, ""))


def _public(address):
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified)


def resolve_and_validate(url):
    p = urlparse(url)
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(p.hostname, p.port or (
            443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise UnsafeURLError("Could not resolve URL hostname") from exc
    if not addresses or any(not _public(address) for address in addresses):
        raise UnsafeURLError("URL resolves to a private or reserved network")
    return sorted(addresses)


def validate_url(url):
    normalized = normalize_url(url)
    resolve_and_validate(normalized)
    return normalized


def fetch(url, **kwargs):
    """Fetch one URL, validating every redirect and streaming at most 10MB."""
    settings = get_settings()
    current = validate_url(url)
    timeout = httpx.Timeout(connect=7, read=15, write=15, pool=7)
    with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False, headers={"User-Agent": settings.user_agent}) as client:
        for hop in range(settings.max_redirects + 1):
            started = time.perf_counter()
            with client.stream("GET", current, **kwargs) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise UnsafeURLError("Redirect has no location")
                    current = validate_url(urljoin(current, location))
                    continue
                chunks = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > settings.max_body_bytes:
                        raise UnsafeURLError(
                            "Response body exceeds the 10MB limit")
                    chunks.append(chunk)
                content = b"".join(chunks)
                response._content = content
                response._content_consumed = True
                return response, current, (time.perf_counter() - started) * 1000
    raise UnsafeURLError("Too many redirects")
