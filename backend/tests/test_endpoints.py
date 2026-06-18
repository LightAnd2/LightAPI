"""API tests for endpoint CRUD, validation, and the SDK ingest flow."""


def test_list_endpoints_empty(client):
    resp = client.get("/api/endpoints")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_endpoint(client):
    resp = client.post(
        "/api/endpoints",
        json={
            "url": "https://api.example.com",
            "name": "example",
            "check_interval": 60,
            "alert_threshold": 300,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "example"
    assert body["url"] == "https://api.example.com"
    assert body["check_interval"] == 60
    assert body["alert_threshold"] == 300
    assert body["current_status"] == "unknown"  # no readings yet
    assert "id" in body


def test_create_endpoint_uses_defaults(client):
    resp = client.post(
        "/api/endpoints",
        json={"url": "https://api.example.com", "name": "defaults"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["check_interval"] == 30
    assert body["alert_threshold"] == 500


def test_create_endpoint_validation_error(client):
    # Missing required "name" field -> 422 from pydantic.
    resp = client.post("/api/endpoints", json={"url": "https://api.example.com"})
    assert resp.status_code == 422


def test_list_after_create(client, sample_endpoint):
    resp = client.get("/api/endpoints")
    assert resp.status_code == 200
    names = [e["name"] for e in resp.json()]
    assert "example-api" in names


def test_get_endpoint_detail(client, sample_endpoint):
    resp = client.get(f"/api/endpoints/{sample_endpoint['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_endpoint["id"]


def test_get_endpoint_404(client):
    resp = client.get("/api/endpoints/does-not-exist")
    assert resp.status_code == 404


def test_delete_endpoint(client, sample_endpoint):
    resp = client.delete(f"/api/endpoints/{sample_endpoint['id']}")
    assert resp.status_code == 204
    # Confirm it's gone.
    assert client.get(f"/api/endpoints/{sample_endpoint['id']}").status_code == 404


def test_delete_missing_endpoint_404(client):
    resp = client.delete("/api/endpoints/does-not-exist")
    assert resp.status_code == 404


def test_readings_for_missing_endpoint_404(client):
    resp = client.get("/api/endpoints/nope/readings")
    assert resp.status_code == 404


def test_readings_empty_for_new_endpoint(client, sample_endpoint):
    resp = client.get(f"/api/endpoints/{sample_endpoint['id']}/readings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_global_stats(client, sample_endpoint):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_endpoints"] == 1
    assert body["active_incidents"] == 0
    assert "global_uptime" in body


def test_ingest_creates_endpoint_and_reading(client):
    """
    Regression test: /api/ingest must persist a reading. This previously crashed
    with a NameError because save_reading was not imported in app.main.
    """
    resp = client.post(
        "/api/ingest",
        json={"name": "checkout", "latency_ms": 42.5, "status_code": 200},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "accepted"
    endpoint_id = body["endpoint_id"]

    # The reading should now be retrievable.
    readings = client.get(f"/api/endpoints/{endpoint_id}/readings").json()
    assert len(readings) == 1
    assert readings[0]["latency_ms"] == 42.5


def test_ingest_matches_existing_endpoint(client, sample_endpoint):
    # "example" matches the sample endpoint named "example-api" by substring.
    resp = client.post(
        "/api/ingest",
        json={"name": "example", "latency_ms": 99.0},
    )
    assert resp.status_code == 202
    assert resp.json()["endpoint_id"] == sample_endpoint["id"]
