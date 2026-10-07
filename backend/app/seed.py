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
        "url": "https://httpbin.org/get",
        "name": "httpbin",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://jsonplaceholder.typicode.com/posts/1",
        "name": "jsonplaceholder",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://www.githubstatus.com/api/v2/status.json",
        "name": "github-status",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://www.cloudflarestatus.com/api/v2/status.json",
        "name": "cloudflare-status",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://pokeapi.co/api/v2/pokemon/1",
        "name": "pokeapi",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://dog.ceo/api/breeds/image/random",
        "name": "dog-ceo",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://catfact.ninja/fact",
        "name": "catfact",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://api.open-meteo.com/v1/forecast?latitude=29.65&longitude=-82.32&current_weather=true",
        "name": "open-meteo",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://api.coinbase.com/v2/prices/spot?currency=USD",
        "name": "coinbase-spot",
        "check_interval": 30,
        "alert_threshold": 500,
    },
    {
        "url": "https://api.chucknorris.io/jokes/random",
        "name": "chucknorris",
        "check_interval": 30,
        "alert_threshold": 500,
    },
]


def seed_if_empty(db: Session):
    existing = get_all_endpoints(db)
    if existing:
        return
    for ep in DEMO_ENDPOINTS:
        create_endpoint(db, ep["url"], ep["name"], ep["check_interval"], ep["alert_threshold"], None)
    logger.info(f"Seeded {len(DEMO_ENDPOINTS)} demo endpoints on first run")
