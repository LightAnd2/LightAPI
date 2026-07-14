import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from db.models import init_db, get_db
from db.deploy_models import DeployEvent
from db.queries import (
    get_all_endpoints, get_endpoint, create_endpoint, delete_endpoint,
    get_readings, get_incidents, get_anomalies, compute_uptime,
    get_incidents_this_month, get_latest_reading, get_model_info,
    get_recent_readings, get_reading_count, get_global_stats, save_reading
)
# ml.predictor / ml.retrain (torch) are imported lazily where used so the app
# can be imported and tested without the heavy ML dependencies installed.
from app.monitor import scheduler, schedule_endpoint, unschedule_endpoint
from app.websocket import manager
from app.seed import seed_if_empty
from app.rca import analyze_incident
from app.drift import detect_drift, check_all_drift
from app.github_webhook import router as github_router
from app.security import validate_public_url, require_ingest_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from db.models import Base, engine
    from db.deploy_models import DeployEvent
    from ml.retrain import retrain_all_endpoints
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(retrain_all_endpoints, "interval", hours=24, id="daily_retrain", coalesce=True)
    scheduler.start()
    db = next(get_db())
    try:
        seed_if_empty(db)
        endpoints = get_all_endpoints(db)
        for ep in endpoints:
            schedule_endpoint(ep.id, ep.url, ep.name, ep.check_interval, ep.alert_threshold, ep.webhook_url, ep.workspace_id)
        logger.info(f"Scheduled {len(endpoints)} endpoints for monitoring")
    finally:
        db.close()
    yield
    scheduler.shutdown()


app = FastAPI(title="LightAI API", lifespan=lifespan)

# Lock CORS to known frontends. Override in production via ALLOWED_ORIGINS
# (comma-separated). Defaults cover the deployed site and local dev.
_default_origins = "https://lightai-kohl.vercel.app,http://localhost:3000,http://localhost:5173"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github_router)


class EndpointCreate(BaseModel):
    url: str
    name: str
    check_interval: int = 30
    alert_threshold: int = 500
    webhook_url: Optional[str] = None


@app.post("/api/workspaces", status_code=201)
def create_workspace():
    """
    Mint a new workspace id. Workspaces are implicit — an id simply namespaces
    the endpoints created under it, giving each visitor their own space without
    accounts or passwords (the shareable-link model).

    The id is the capability: anyone who has it can access the workspace, so it
    must be unguessable. 96 bits of cryptographic randomness makes enumeration
    infeasible.
    """
    import secrets
    return {"id": secrets.token_urlsafe(12)}


def endpoint_to_dict(ep, db: Session) -> dict:
    latest = get_latest_reading(db, ep.id)
    current_latency = latest.latency_ms if latest else None
    last_checked = latest.timestamp.isoformat() if latest else None

    if latest is None:
        status = "unknown"
    elif not latest.success:
        status = "down"
    elif latest.latency_ms and latest.latency_ms > ep.alert_threshold:
        status = "degraded"
    else:
        status = "healthy"

    uptime_24h = compute_uptime(db, ep.id, 1)

    return {
        "id": ep.id,
        "url": ep.url,
        "name": ep.name,
        "check_interval": ep.check_interval,
        "alert_threshold": ep.alert_threshold,
        "webhook_url": ep.webhook_url,
        "is_active": ep.is_active,
        "created_at": ep.created_at.isoformat(),
        "current_status": status,
        "current_latency": current_latency,
        "last_checked": last_checked,
        "uptime_24h": uptime_24h,
    }


@app.get("/api/endpoints")
def list_endpoints(workspace: str = "demo", db: Session = Depends(get_db)):
    endpoints = get_all_endpoints(db, workspace)
    return [endpoint_to_dict(ep, db) for ep in endpoints]


@app.post("/api/endpoints", status_code=201)
def add_endpoint(body: EndpointCreate, workspace: str = "demo", db: Session = Depends(get_db)):
    validate_public_url(body.url)
    ep = create_endpoint(db, body.url, body.name, body.check_interval, body.alert_threshold, body.webhook_url, workspace_id=workspace)
    schedule_endpoint(ep.id, ep.url, ep.name, ep.check_interval, ep.alert_threshold, ep.webhook_url, ep.workspace_id)
    return endpoint_to_dict(ep, db)


@app.get("/api/endpoints/{endpoint_id}")
def get_endpoint_detail(endpoint_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    return endpoint_to_dict(ep, db)


@app.delete("/api/endpoints/{endpoint_id}", status_code=204)
def remove_endpoint(endpoint_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    # The demo workspace is the only publicly-known one — protect its seeded
    # endpoints from vandalism. Visitors can still add and monitor endpoints.
    if ep.workspace_id == "demo":
        raise HTTPException(403, "Demo endpoints can't be deleted — create your own workspace")
    unschedule_endpoint(endpoint_id)
    delete_endpoint(db, endpoint_id)


@app.get("/api/endpoints/{endpoint_id}/readings")
def endpoint_readings(endpoint_id: str, range: str = "24h", db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    rows = get_readings(db, endpoint_id, range)
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "latency_ms": r.latency_ms,
            "status_code": r.status_code,
            "success": r.success,
        }
        for r in rows
    ]


@app.get("/api/endpoints/{endpoint_id}/incidents")
def endpoint_incidents(endpoint_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    incidents = get_incidents(db, endpoint_id)
    return [
        {
            "id": inc.id,
            "started_at": inc.started_at.isoformat(),
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            "peak_latency": inc.peak_latency,
            "severity": inc.severity,
            "is_resolved": inc.is_resolved,
            "duration_seconds": (
                (inc.resolved_at - inc.started_at).total_seconds()
                if inc.resolved_at else None
            ),
        }
        for inc in incidents
    ]


@app.get("/api/endpoints/{endpoint_id}/anomalies")
def endpoint_anomalies(endpoint_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    events = get_anomalies(db, endpoint_id)
    return [
        {
            "id": ev.id,
            "timestamp": ev.timestamp.isoformat(),
            "confidence": ev.confidence,
            "predicted_latency": ev.predicted_latency,
            "actual_latency": ev.actual_latency,
        }
        for ev in events
    ]


@app.get("/api/endpoints/{endpoint_id}/stats")
def endpoint_stats(endpoint_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    latest = get_latest_reading(db, endpoint_id)
    return {
        "current_latency": latest.latency_ms if latest else None,
        "uptime_7d": compute_uptime(db, endpoint_id, 7),
        "uptime_30d": compute_uptime(db, endpoint_id, 30),
        "incidents_month": get_incidents_this_month(db, endpoint_id),
        "reading_count": get_reading_count(db, endpoint_id),
        "model_ready": (get_model_info(db, endpoint_id) or {}).is_ready if get_model_info(db, endpoint_id) else False,
    }


@app.get("/api/endpoints/{endpoint_id}/predictions")
def endpoint_predictions(endpoint_id: str, steps: int = 30, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    model_info = get_model_info(db, endpoint_id)
    if not model_info or not model_info.is_ready:
        return {"predictions": [], "model_ready": False}
    recent = get_recent_readings(db, endpoint_id, limit=60)
    latencies = [r.latency_ms for r in reversed(recent) if r.latency_ms is not None]
    from ml.predictor import predict_future
    preds = predict_future(model_info.model_path, model_info.scaler_path, latencies, steps)
    return {"predictions": preds, "model_ready": True}


class IngestPayload(BaseModel):
    name: str
    endpoint_id: Optional[str] = None
    workspace: str = "demo"
    timestamp: Optional[str] = None
    latency_ms: float
    success: bool = True
    status_code: int = 200
    threshold_ms: Optional[int] = None
    source: str = "sdk"


@app.post("/api/ingest", status_code=202)
async def ingest(payload: IngestPayload, db: Session = Depends(get_db), _: None = Depends(require_ingest_key)):
    ep = None
    if payload.endpoint_id:
        ep = get_endpoint(db, payload.endpoint_id)
    if not ep:
        endpoints = get_all_endpoints(db, payload.workspace)
        for e in endpoints:
            if payload.name.lower() in e.name.lower() or payload.name.lower() in e.url.lower():
                ep = e
                break
    if not ep:
        ep = create_endpoint(
            db,
            url=f"sdk://{payload.name}",
            name=payload.name,
            check_interval=0,
            alert_threshold=payload.threshold_ms or 500,
            webhook_url=None,
            workspace_id=payload.workspace,
        )

    reading = save_reading(db, ep.id, payload.latency_ms, payload.status_code, payload.success)
    message = {
        "type": "reading",
        "endpoint_id": ep.id,
        "data": {
            "timestamp": reading.timestamp.isoformat(),
            "latency_ms": payload.latency_ms,
            "status_code": payload.status_code,
            "success": payload.success,
            "source": "sdk",
            "anomaly": None,
            "incident": None,
        },
    }
    await manager.broadcast(message, ep.id, ep.workspace_id)
    return {"status": "accepted", "endpoint_id": ep.id}


@app.get("/api/stats")
def global_stats(workspace: str = "demo", db: Session = Depends(get_db)):
    stats = get_global_stats(db, workspace)
    endpoints = get_all_endpoints(db, workspace)
    uptimes = [compute_uptime(db, ep.id, 1) for ep in endpoints]
    global_uptime = round(sum(uptimes) / len(uptimes), 2) if uptimes else 100.0
    stats["global_uptime"] = global_uptime
    return stats


@app.get("/api/endpoints/{endpoint_id}/rca/{incident_id}")
def endpoint_rca(endpoint_id: str, incident_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    from db.queries import get_incidents
    incidents = get_incidents(db, endpoint_id)
    inc = next((i for i in incidents if i.id == incident_id), None)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return analyze_incident(db, endpoint_id, inc.started_at)


@app.get("/api/endpoints/{endpoint_id}/drift")
def endpoint_drift(endpoint_id: str, db: Session = Depends(get_db)):
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        raise HTTPException(404, "Endpoint not found")
    result = detect_drift(db, endpoint_id)
    if result is None:
        return {"status": "insufficient_data", "message": "Not enough readings yet to detect drift (need 30 days of data)."}
    return result


@app.get("/api/drift")
def all_drift(workspace: str = "demo", db: Session = Depends(get_db)):
    return check_all_drift(db, workspace)


@app.websocket("/ws/{endpoint_id}")
async def websocket_endpoint(websocket: WebSocket, endpoint_id: str):
    await manager.connect(websocket, endpoint_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, endpoint_id)


@app.websocket("/ws")
async def websocket_global(websocket: WebSocket, workspace: str = "demo"):
    await manager.connect_global(websocket, workspace)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_global(websocket, workspace)
