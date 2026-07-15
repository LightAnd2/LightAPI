"""Tests for abuse/DoS hardening: rate limits, caps, and input bounds."""
import app.main as main


def _create(client, ws, name, i):
    return client.post(f"/api/endpoints?workspace={ws}", json={"url": f"https://ex{i}.example.com", "name": name})


def test_endpoint_cap_per_workspace(client, monkeypatch):
    # Keep the cap low for a fast test.
    monkeypatch.setattr(main, "MAX_ENDPOINTS_PER_WORKSPACE", 3)
    for i in range(3):
        assert _create(client, "capws", f"e{i}", i).status_code == 201
    # The 4th is rejected.
    assert _create(client, "capws", "e4", 4).status_code == 429


def test_rate_limit_on_workspace_mint(client):
    # RateLimiter(20, 60) on /api/workspaces — the 21st within the window trips.
    codes = [client.post("/api/workspaces").status_code for _ in range(25)]
    assert codes.count(201) == 20
    assert 429 in codes


def test_oversized_input_rejected(client):
    huge = "x" * 5000
    resp = client.post("/api/endpoints?workspace=w", json={"url": f"https://a.com/{huge}", "name": "n"})
    assert resp.status_code == 422  # exceeds url max_length


def test_check_interval_bounds(client):
    # check_interval below the floor (10s) is rejected — prevents hammering targets.
    resp = client.post("/api/endpoints?workspace=w", json={"url": "https://a.example.com", "name": "n", "check_interval": 1})
    assert resp.status_code == 422


def test_directory_offset_bounds(client):
    assert client.get("/api/directory?offset=-1").status_code == 422
    assert client.get("/api/directory?limit=99999").status_code == 422


def test_security_headers_present(client):
    r = client.get("/api/directory/categories")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
