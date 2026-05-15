"""
First-run seed — if the DB is empty, add a few simulator endpoints as demos.
Runs once on startup. Never overwrites existing data.
"""
import logging
from sqlalchemy.orm import Session
from db.queries import get_all_endpoints, create_endpoint

logger = logging.getLogger(__name__)

DEMO_ENDPOINTS = [
    {
        "url": "http://localhost:8001/sim/auth_service_1",
        "name": "auth-service",
        "check_interval": 30,
        "alert_threshold": 300,
    },
    {
        "url": "http://localhost:8001/sim/cdn_edge_4",
        "name": "cdn-edge",
        "check_interval": 30,
        "alert_threshold": 100,
    },
    {
        "url": "http://localhost:8001/sim/payments_api_2",
        "name": "payments-api",
        "check_interval": 30,
        "alert_threshold": 600,
    },
]


def seed_if_empty(db: Session):
    existing = get_all_endpoints(db)
    if existing:
        return
    for ep in DEMO_ENDPOINTS:
        create_endpoint(db, ep["url"], ep["name"], ep["check_interval"], ep["alert_threshold"], None)
    logger.info(f"Seeded {len(DEMO_ENDPOINTS)} demo endpoints on first run")
