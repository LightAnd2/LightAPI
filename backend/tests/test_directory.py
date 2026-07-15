"""Tests for the public API directory (discovery) — parsing, search, filters."""
import pytest

from db.models import DirectoryApi
from app.directory import parse_readme


SAMPLE_README = """\
### Animals
API | Description | Auth | HTTPS | CORS
|:---|:---|:---|:---|:---|
| [Cat Facts](https://catfact.ninja/) | Random cat facts | No | Yes | Yes |
| [Dogs](https://dog.ceo/dog-api/) | Dog images | No | Yes | Yes |

### Cryptocurrency
API | Description | Auth | HTTPS | CORS
|:---|:---|:---|:---|:---|
| [CoinGecko](https://www.coingecko.com/en/api) | Crypto prices | No | Yes | Yes |
| [Nomics](https://nomics.com/) | Crypto market data | `apiKey` | Yes | Unknown |

### Index
Some non-API filler that must be ignored.
"""


def test_parse_readme_extracts_apis():
    entries = parse_readme(SAMPLE_README)
    names = {e["name"] for e in entries}
    assert names == {"Cat Facts", "Dogs", "CoinGecko", "Nomics"}


def test_parse_readme_fields():
    entries = {e["name"]: e for e in parse_readme(SAMPLE_README)}
    nomics = entries["Nomics"]
    assert nomics["category"] == "Cryptocurrency"
    assert nomics["auth"] == "apiKey"
    assert nomics["https"] is True
    assert nomics["cors"] == "unknown"  # "Unknown" normalized
    assert entries["Cat Facts"]["auth"] == "None"  # "No" normalized


def test_parse_readme_skips_meta_sections():
    entries = parse_readme(SAMPLE_README)
    assert all(e["category"] != "Index" for e in entries)


def _seed(client, rows):
    db = client.session_factory()
    try:
        db.bulk_insert_mappings(DirectoryApi, rows)
        db.commit()
    finally:
        db.close()


ROWS = [
    {"name": "Cat Facts", "url": "https://catfact.ninja/", "description": "Random cat facts",
     "auth": "None", "https": True, "cors": "yes", "category": "Animals"},
    {"name": "CoinGecko", "url": "https://coingecko.com/", "description": "Crypto prices",
     "auth": "None", "https": True, "cors": "yes", "category": "Cryptocurrency"},
    {"name": "Nomics", "url": "https://nomics.com/", "description": "Crypto market data",
     "auth": "apiKey", "https": True, "cors": "unknown", "category": "Cryptocurrency"},
]


def test_directory_lists_all(client):
    _seed(client, ROWS)
    body = client.get("/api/directory").json()
    assert body["total"] == 3
    assert len(body["results"]) == 3


def test_directory_filter_by_category(client):
    _seed(client, ROWS)
    body = client.get("/api/directory?category=Cryptocurrency").json()
    assert body["total"] == 2
    assert {r["name"] for r in body["results"]} == {"CoinGecko", "Nomics"}


def test_directory_search(client):
    _seed(client, ROWS)
    body = client.get("/api/directory?search=cat").json()
    assert body["total"] == 1
    assert body["results"][0]["name"] == "Cat Facts"


def test_directory_filter_no_auth(client):
    _seed(client, ROWS)
    body = client.get("/api/directory?auth=none").json()
    assert {r["name"] for r in body["results"]} == {"Cat Facts", "CoinGecko"}


def test_directory_categories_with_counts(client):
    _seed(client, ROWS)
    body = client.get("/api/directory/categories").json()
    assert body["total"] == 3
    counts = {c["category"]: c["count"] for c in body["categories"]}
    assert counts == {"Animals": 1, "Cryptocurrency": 2}


def test_directory_empty_when_unseeded(client):
    body = client.get("/api/directory").json()
    assert body == {"total": 0, "results": []}


def test_snapshot_file_is_valid_and_substantial():
    """The bundled snapshot must exist and cover a real dataset."""
    import json, os
    path = os.path.join(os.path.dirname(__file__), "..", "data", "apis_snapshot.json")
    data = json.load(open(path))
    assert len(data) > 1000
    assert {"name", "url", "category", "auth", "https", "cors"} <= set(data[0])
