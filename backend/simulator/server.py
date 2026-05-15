"""
Synthetic endpoint server — spins up fake HTTP endpoints that respond with
procedurally generated latency. Auto-registers with LightAI on startup.
"""
import asyncio
import random
import time
import httpx
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simulator.profiles import generate_profiles
from simulator.engine import generate_latency

logger = logging.getLogger(__name__)

SIM_PORT = 8001
LIGHTAI_API = "http://localhost:8000"
DEFAULT_COUNT = 10
DEFAULT_SEED = 42

app = FastAPI(title="LightAI Load Simulator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_profiles = generate_profiles(DEFAULT_COUNT, DEFAULT_SEED)
_rngs = {p.id: random.Random(DEFAULT_SEED + p.id) for p in _profiles}
_start_time = time.monotonic()
_registered_ids = {}


def _elapsed_minutes() -> float:
    return (time.monotonic() - _start_time) / 60.0


def _make_handler(profile):
    async def handler():
        latency, success = generate_latency(profile, _rngs[profile.id], _elapsed_minutes())
        if not success:
            from fastapi import Response
            await asyncio.sleep(0.5)
            return Response(status_code=503, content="Service Unavailable")
        await asyncio.sleep(latency / 1000.0)
        return {
            "service": profile.name,
            "latency_ms": latency,
            "status": "ok",
            "baseline_ms": round(profile.baseline_ms, 1),
        }
    handler.__name__ = f"handler_{profile.name}"
    return handler


for profile in _profiles:
    app.add_api_route(profile.path, _make_handler(profile), methods=["GET"])


@app.get("/sim/status")
def status():
    return {
        "services": len(_profiles),
        "uptime_minutes": round(_elapsed_minutes(), 1),
        "registered_in_lightai": len(_registered_ids),
        "endpoints": [
            {
                "name": p.name,
                "path": p.path,
                "baseline_ms": round(p.baseline_ms, 1),
                "degradation_events": len(p.degradation_schedule),
            }
            for p in _profiles
        ],
    }


async def register_with_lightai():
    await asyncio.sleep(2)
    async with httpx.AsyncClient(timeout=10.0) as client:
        existing = []
        try:
            r = await client.get(f"{LIGHTAI_API}/api/endpoints")
            existing = [ep["name"] for ep in r.json()]
        except Exception:
            pass

        for profile in _profiles:
            if profile.name in existing:
                logger.info(f"Simulator: {profile.name} already registered")
                continue
            try:
                payload = {
                    "url": f"http://localhost:{SIM_PORT}{profile.path}",
                    "name": profile.name,
                    "check_interval": 30,
                    "alert_threshold": int(profile.baseline_ms * 2.5),
                    "webhook_url": None,
                }
                r = await client.post(f"{LIGHTAI_API}/api/endpoints", json=payload)
                if r.status_code == 201:
                    ep = r.json()
                    _registered_ids[profile.name] = ep["id"]
                    logger.info(f"Simulator: registered {profile.name} → {ep['id']}")
            except Exception as e:
                logger.warning(f"Simulator: failed to register {profile.name}: {e}")


@app.on_event("startup")
async def startup():
    asyncio.create_task(register_with_lightai())
    logger.info(f"Simulator running {len(_profiles)} synthetic services on port {SIM_PORT}")
