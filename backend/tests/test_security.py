"""Tests for SSRF protection and ingest API-key auth."""
import pytest
from fastapi import HTTPException

import app.security as security
from app.security import validate_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata endpoint
        "http://127.0.0.1:8000",                      # loopback
        "http://localhost/admin",                     # loopback by name
        "http://10.0.0.5/internal",                   # private range
        "http://192.168.1.1",                         # private range
        "http://[::1]:9000",                          # IPv6 loopback
        "ftp://example.com/file",                     # disallowed scheme
        "file:///etc/passwd",                         # disallowed scheme
        "not-a-url",                                  # no host
    ],
)
def test_validate_public_url_rejects_unsafe(url):
    with pytest.raises(HTTPException) as exc:
        validate_public_url(url)
    assert exc.value.status_code == 400


def test_ingest_requires_key_when_configured(client, monkeypatch):
    monkeypatch.setattr(security, "INGEST_API_KEY", "secret-key")

    # No key -> rejected.
    resp = client.post("/api/ingest", json={"name": "svc", "latency_ms": 10.0})
    assert resp.status_code == 401

    # Wrong key -> rejected.
    resp = client.post(
        "/api/ingest",
        json={"name": "svc", "latency_ms": 10.0},
        headers={"X-API-Key": "nope"},
    )
    assert resp.status_code == 401

    # Correct key -> accepted.
    resp = client.post(
        "/api/ingest",
        json={"name": "svc", "latency_ms": 10.0},
        headers={"X-API-Key": "secret-key"},
    )
    assert resp.status_code == 202


def test_ingest_open_when_key_unset(client, monkeypatch):
    monkeypatch.setattr(security, "INGEST_API_KEY", "")
    resp = client.post("/api/ingest", json={"name": "svc", "latency_ms": 10.0})
    assert resp.status_code == 202
