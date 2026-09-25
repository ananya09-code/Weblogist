"""URL validation and SSRF protections for outbound requests."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

MAX_REDIRECTS = 5
ALLOWED_SCHEMES = {"http", "https"}


class UnsafeURLError(ValueError):
    """Raised when a URL is malformed or targets a non-public network."""


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise UnsafeURLError("URL cannot be empty")
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError("Only http and https URLs are supported")
    if not parsed.hostname or parsed.username or parsed.password:
        raise UnsafeURLError("A valid public HTTP(S) URL is required")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeURLError("Invalid URL port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise UnsafeURLError("Invalid URL port")
    # Lowercase host but preserve user path/query; remove fragments from cache identity.
    host = parsed.hostname.encode("idna").decode("ascii")
    if ":" in host:
        host = f"[{host}]"
    netloc = host + (f":{port}" if port else "")
    return urlunparse((parsed.scheme.lower(), netloc, parsed.path or "/", parsed.params, parsed.query, ""))


def _is_public(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified)


def resolve_and_validate(url: str) -> list[str]:
    """Resolve a host and ensure every address is public.

    The address list is returned so callers can optionally connect to the
    validated address when they need to close DNS-rebinding gaps.
    """
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no hostname")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise UnsafeURLError("Could not resolve URL hostname") from exc
    if not addresses or any(not _is_public(address) for address in addresses):
        raise UnsafeURLError("URL resolves to a private or reserved network")
    return sorted(addresses)


def validate_url(url: str) -> str:
    normalized = normalize_url(url)
    resolve_and_validate(normalized)
    return normalized
