"""
Shared pytest fixtures.

Each test runs against a fresh in-memory SQLite database and a TestClient that
never starts the background scheduler — so tests are fast, isolated, and make no
real network calls.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, get_db
import app.main as main


@pytest.fixture
def client(monkeypatch):
    # In-memory DB shared across connections for the duration of one test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Stub the scheduler hooks so creating/deleting endpoints doesn't touch
    # APScheduler or fire real HTTP checks during tests.
    monkeypatch.setattr(main, "schedule_endpoint", lambda *a, **k: None)
    monkeypatch.setattr(main, "unschedule_endpoint", lambda *a, **k: None)
    # Stub SSRF URL validation for CRUD tests so they don't depend on DNS.
    # SSRF behaviour is covered directly in test_security.py.
    monkeypatch.setattr(main, "validate_public_url", lambda *a, **k: None)

    # Reset per-IP rate-limiter state so counts don't leak across tests
    # (all TestClient requests share one client IP).
    for lim in (main.workspace_limiter, main.endpoint_limiter, main.ingest_limiter):
        lim._hits.clear()

    main.app.dependency_overrides[get_db] = override_get_db
    # TestClient is NOT used as a context manager, so the app's lifespan
    # (scheduler start + seeding) never runs.
    tc = TestClient(main.app)
    tc.session_factory = TestingSessionLocal  # exposed so tests can seed rows
    yield tc
    main.app.dependency_overrides.clear()


SAMPLE_WS = "test-ws"


@pytest.fixture
def db_session():
    """A raw DB session on a fresh in-memory database, for testing helpers directly."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_endpoint(client):
    """Create one endpoint in a private (non-demo) workspace and return its JSON."""
    resp = client.post(
        f"/api/endpoints?workspace={SAMPLE_WS}",
        json={"url": "https://example.com/health", "name": "example-api"},
    )
    assert resp.status_code == 201
    return resp.json()
