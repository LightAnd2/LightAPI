"""
Security helpers: SSRF protection and optional SDK ingest authentication.

The dashboard itself is a public demo (no login), so these guards protect the
two genuinely abusable surfaces:

  * SSRF — anyone can add a URL to monitor, and the server then makes requests
    to it. Without validation that lets an attacker point LightAI at internal
    services (cloud metadata endpoints, localhost, private network ranges).
  * Ingest — the SDK ingest endpoint can be protected with a shared API key so
    only your instrumented services can push readings in production.
"""
import ipaddress
import os
import socket
from urllib.parse import urlparse

from fastapi import Header, HTTPException

INGEST_API_KEY = os.getenv("LIGHTAI_API_KEY", "")


def validate_public_url(url: str) -> None:
    """
    Raise HTTPException(400) unless `url` is an http(s) URL whose host resolves
    only to public IP addresses. Blocks SSRF against loopback, private, and
    link-local ranges (including the cloud metadata IP 169.254.169.254).
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "URL must use http or https")

    host = parsed.hostname
    if not host:
        raise HTTPException(400, "URL must include a host")

    try:
        # Resolve every address the host maps to; reject if any is non-public.
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise HTTPException(400, "URL host could not be resolved")

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if not ip.is_global or ip.is_loopback or ip.is_link_local or ip.is_private:
            raise HTTPException(400, "URL resolves to a non-public address")


def require_ingest_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    FastAPI dependency. If LIGHTAI_API_KEY is configured, require a matching
    X-API-Key header. If it is unset (e.g. local dev), ingest is open.
    """
    if not INGEST_API_KEY:
        return
    if x_api_key != INGEST_API_KEY:
        raise HTTPException(401, "Invalid or missing API key")
