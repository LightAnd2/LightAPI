"""
Public API directory — the discovery core of LightAPI.

Data is sourced from the community-maintained public-apis project. A bundled
JSON snapshot seeds the database instantly on first boot (so the app works with
no network), and a daily scheduler job refreshes it from GitHub so newly added
APIs appear automatically.
"""
import json
import logging
import os
import re

import httpx
from sqlalchemy.orm import Session

from db.models import DirectoryApi

logger = logging.getLogger(__name__)

PUBLIC_APIS_README = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "apis_snapshot.json")

# Section headings in the README that are not real API categories.
_SKIP_CATEGORIES = {"Index", "Contributing", "License", "APIs Covered Under APILayer Suite!"}

_ROW_RE = re.compile(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|(.*)$")


def parse_readme(md: str) -> list[dict]:
    """Parse the public-apis README markdown into a list of API dicts."""
    entries: list[dict] = []
    category = None
    in_table = False

    for line in md.splitlines():
        if line.startswith("### "):
            category = line[4:].strip()
            in_table = False
            continue
        if category and line.strip().startswith("API | Description"):
            in_table = True
            continue
        if not in_table:
            continue

        m = _ROW_RE.match(line.strip())
        if not m:
            if line.strip() == "" or line.startswith("###"):
                in_table = False
            continue

        name, url, rest = m.group(1).strip(), m.group(2).strip(), m.group(3)
        cols = [c.strip() for c in rest.split("|")]
        desc = cols[0] if len(cols) > 0 else ""
        auth_raw = cols[1].replace("`", "").strip() if len(cols) > 1 else ""
        https = (cols[2].strip().lower() == "yes") if len(cols) > 2 else False
        cors_raw = cols[3].strip().lower() if len(cols) > 3 else "unknown"

        if category in _SKIP_CATEGORIES or not url.startswith("http"):
            continue

        entries.append({
            "name": name,
            "url": url,
            "description": desc,
            "auth": "None" if auth_raw in ("", "No") else auth_raw,
            "https": https,
            "cors": cors_raw if cors_raw in ("yes", "no") else "unknown",
            "category": category,
        })
    return entries


def _load_snapshot() -> list[dict]:
    try:
        with open(SNAPSHOT_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Directory snapshot unavailable: {e}")
        return []


def _replace_directory(db: Session, entries: list[dict]) -> int:
    """Atomically swap the directory contents for a fresh set of entries."""
    if not entries:
        return 0
    db.query(DirectoryApi).delete()
    db.bulk_insert_mappings(DirectoryApi, entries)
    db.commit()
    return len(entries)


def seed_directory_if_empty(db: Session) -> None:
    """On first boot, populate the directory from the bundled snapshot."""
    if db.query(DirectoryApi.id).first():
        return
    count = _replace_directory(db, _load_snapshot())
    if count:
        logger.info(f"Seeded API directory with {count} APIs from snapshot")


async def refresh_directory_from_github(db: Session) -> int:
    """
    Fetch the latest public-apis README and rebuild the directory. On any
    failure the existing directory is left untouched.
    """
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(PUBLIC_APIS_README)
            resp.raise_for_status()
        entries = parse_readme(resp.text)
    except Exception as e:
        logger.warning(f"Directory refresh failed, keeping existing data: {e}")
        return 0

    if len(entries) < 500:  # sanity guard against a malformed/partial fetch
        logger.warning(f"Directory refresh returned only {len(entries)} APIs — skipping swap")
        return 0

    count = _replace_directory(db, entries)
    logger.info(f"Refreshed API directory: {count} APIs")
    return count
