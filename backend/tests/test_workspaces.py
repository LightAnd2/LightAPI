"""Tests for workspace isolation — each workspace only sees its own endpoints."""


def _create(client, workspace, name):
    resp = client.post(
        f"/api/endpoints?workspace={workspace}",
        json={"url": f"https://{name}.example.com", "name": name},
    )
    assert resp.status_code == 201
    return resp.json()


def test_create_workspace_mints_id(client):
    resp = client.post("/api/workspaces")
    assert resp.status_code == 201
    ws_id = resp.json()["id"]
    # 96 bits of randomness -> 16 urlsafe chars. The id is the capability, so
    # it must be long enough to be unguessable.
    assert isinstance(ws_id, str) and len(ws_id) >= 16

    # Ids are unique across calls.
    assert client.post("/api/workspaces").json()["id"] != ws_id


def _seed_demo_endpoint(client, name="demo-ep"):
    from db.queries import create_endpoint
    db = client.session_factory()
    try:
        ep = create_endpoint(db, "https://d.example.com", name, 30, 500, None, workspace_id="demo")
        return ep.id
    finally:
        db.close()


def test_demo_endpoints_cannot_be_deleted(client):
    # demo is the only publicly-known workspace; its endpoints are protected.
    ep_id = _seed_demo_endpoint(client)
    assert client.delete(f"/api/endpoints/{ep_id}").status_code == 403
    # Still there.
    assert [e["id"] for e in client.get("/api/endpoints").json()] == [ep_id]


def test_demo_workspace_is_read_only(client):
    # Writes to the public demo workspace are rejected; visitors use their own.
    assert client.post("/api/endpoints", json={"url": "https://d.example.com", "name": "x"}).status_code == 403
    assert client.post("/api/endpoints?workspace=demo", json={"url": "https://d.example.com", "name": "x"}).status_code == 403
    assert client.post("/api/ingest", json={"name": "x", "latency_ms": 1.0, "workspace": "demo"}).status_code == 403


def test_endpoints_are_isolated_per_workspace(client):
    _create(client, "ws-alpha", "alpha-api")
    _create(client, "ws-beta", "beta-api")

    alpha = [e["name"] for e in client.get("/api/endpoints?workspace=ws-alpha").json()]
    beta = [e["name"] for e in client.get("/api/endpoints?workspace=ws-beta").json()]

    assert alpha == ["alpha-api"]
    assert beta == ["beta-api"]


def test_reads_default_to_demo_workspace(client):
    # No workspace param on a read -> demo namespace (isolated from others).
    _seed_demo_endpoint(client, "seeded-demo")
    names = [e["name"] for e in client.get("/api/endpoints").json()]
    assert names == ["seeded-demo"]
    assert client.get("/api/endpoints?workspace=other").json() == []


def test_global_stats_scoped_to_workspace(client):
    _create(client, "ws-a", "a1")
    _create(client, "ws-a", "a2")
    _create(client, "ws-b", "b1")

    assert client.get("/api/stats?workspace=ws-a").json()["total_endpoints"] == 2
    assert client.get("/api/stats?workspace=ws-b").json()["total_endpoints"] == 1


def test_drift_summary_scoped_to_workspace(client):
    # /api/drift must not leak endpoint names/ids from other workspaces.
    _create(client, "ws-x", "x-only-api")
    resp = client.get("/api/drift?workspace=ws-y")
    assert resp.status_code == 200
    names = [d.get("endpoint_name") for d in resp.json()]
    assert "x-only-api" not in names


def test_webhook_matching_scoped_to_workspace(db_session):
    # A deploy webhook bound to one workspace must never match an endpoint in
    # another, even if the repo name matches.
    from app.github_webhook import _find_matching_endpoint
    from db.queries import create_endpoint

    create_endpoint(db_session, "https://github.com/me/payments", "payments", 30, 500, None, workspace_id="ws-1")

    # Same repo name, but the webhook is bound to a different workspace.
    assert _find_matching_endpoint(db_session, "payments", "someone", "ws-2") is None
    # Bound to the right workspace -> matches.
    assert _find_matching_endpoint(db_session, "payments", "someone", "ws-1") is not None


def test_ingest_scoped_to_workspace(client):
    # Ingest with a workspace creates the endpoint in that workspace only.
    resp = client.post(
        "/api/ingest",
        json={"name": "checkout", "latency_ms": 12.0, "workspace": "ws-sdk"},
    )
    assert resp.status_code == 202

    assert [e["name"] for e in client.get("/api/endpoints?workspace=ws-sdk").json()] == ["checkout"]
    assert client.get("/api/endpoints").json() == []  # demo untouched

    # Same name in a different workspace does NOT match the ws-sdk endpoint.
    resp2 = client.post(
        "/api/ingest",
        json={"name": "checkout", "latency_ms": 15.0, "workspace": "ws-other"},
    )
    assert resp2.status_code == 202
    assert resp2.json()["endpoint_id"] != resp.json()["endpoint_id"]
