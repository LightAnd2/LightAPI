import os
import threading
import urllib.request
import urllib.error
import json
import logging

logger = logging.getLogger(__name__)

_config = {
    "url": os.getenv("LIGHTAI_URL", "http://localhost:8000"),
    "api_key": os.getenv("LIGHTAI_API_KEY", ""),
    "workspace": os.getenv("LIGHTAI_WORKSPACE", "sandbox"),
}


def configure(url: str = None, api_key: str = None, workspace: str = None):
    if url:
        _config["url"] = url.rstrip("/")
    if api_key:
        _config["api_key"] = api_key
    if workspace:
        _config["workspace"] = workspace


def _send(payload: dict):
    try:
        payload.setdefault("workspace", _config["workspace"])
        body = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if _config["api_key"]:
            headers["X-API-Key"] = _config["api_key"]
        req = urllib.request.Request(
            f"{_config['url']}/api/ingest",
            data=body,
            headers=headers,
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
    except Exception as e:
        logger.debug(f"LightAI: failed to send reading — {e}")


def send_async(payload: dict):
    t = threading.Thread(target=_send, args=(payload,), daemon=True)
    t.start()
