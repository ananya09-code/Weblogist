import pytest

from backend.security import UnsafeURLError, _is_public, normalize_url


def test_normalize_url_adds_scheme_and_removes_fragment():
    assert normalize_url(
        "Example.COM/path?q=1#fragment") == "https://example.com/path?q=1"


@pytest.mark.parametrize("value", ["file:///etc/passwd", "ftp://example.com", "https://user:pass@example.com", "https://"])
def test_rejects_unsafe_or_malformed_url(value):
    with pytest.raises(UnsafeURLError):
        normalize_url(value)


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254", "::1", "0.0.0.0"])
def test_private_addresses_are_not_public(address):
    assert not _is_public(address)


def test_public_addresses_are_public():
    assert _is_public("1.1.1.1")
