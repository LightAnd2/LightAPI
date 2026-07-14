import asyncio
import logging
import time
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
import httpx

from db.models import SessionLocal
from db.queries import (
    save_reading, get_recent_readings, get_model_info,
    get_reading_count, update_model_info, save_anomaly
)
# ML (torch) imports are loaded lazily inside the functions that need them, so
# the API process can start without pulling in the heavy ML stack.
from app.websocket import manager
from app.incidents import handle_incident_lifecycle
from app.alerts import send_down_alert, send_anomaly_alert
from app.rca import analyze_incident
from app.drift import detect_drift

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def check_endpoint(endpoint_id: str, url: str, name: str, alert_threshold: int, webhook_url: Optional[str], workspace_id: str = "demo"):
    start = time.monotonic()
    latency_ms: Optional[float] = None
    status_code: Optional[int] = None
    success = False

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
        latency_ms = (time.monotonic() - start) * 1000
        status_code = resp.status_code
        success = resp.status_code < 400
    except Exception:
        pass

    db: Session = SessionLocal()
    try:
        reading = save_reading(db, endpoint_id, latency_ms, status_code, success)

        anomaly_data = None

        if success and latency_ms is not None:
            from ml.lstm import MIN_READINGS
            from ml.predictor import check_anomaly_lstm, check_anomaly_zscore

            model_info = get_model_info(db, endpoint_id)
            recent = get_recent_readings(db, endpoint_id, limit=60)
            recent_latencies = [r.latency_ms for r in reversed(recent) if r.latency_ms is not None]

            if model_info and model_info.is_ready and model_info.model_path:
                is_anomaly, confidence, predicted = check_anomaly_lstm(
                    model_info.model_path, model_info.scaler_path, recent_latencies, latency_ms
                )
            else:
                is_anomaly, confidence = check_anomaly_zscore(recent_latencies, latency_ms)
                predicted = None

            if is_anomaly and confidence > 0.4:
                save_anomaly(db, endpoint_id, confidence, predicted, latency_ms)
                anomaly_data = {"confidence": confidence, "predicted_latency": predicted}
                await send_anomaly_alert(name, url, webhook_url, predicted, latency_ms, confidence)

            count = get_reading_count(db, endpoint_id)
            if count >= MIN_READINGS and (model_info is None or not model_info.is_ready):
                asyncio.create_task(_train_background(endpoint_id))

        incident_result = handle_incident_lifecycle(db, endpoint_id, success, latency_ms, alert_threshold)

        rca_data = None
        if incident_result["opened"] and not success:
            await send_down_alert(name, url, webhook_url)
            rca_data = analyze_incident(db, endpoint_id, reading.timestamp)

        drift_data = detect_drift(db, endpoint_id)

        message = {
            "type": "reading",
            "endpoint_id": endpoint_id,
            "data": {
                "timestamp": reading.timestamp.isoformat(),
                "latency_ms": latency_ms,
                "status_code": status_code,
                "success": success,
                "anomaly": anomaly_data,
                "incident": incident_result,
                "rca": rca_data,
                "drift": drift_data if drift_data and drift_data.get("status") not in ("stable", "insufficient_data") else None,
            },
        }
        await manager.broadcast(message, endpoint_id, workspace_id)
    finally:
        db.close()


async def _train_background(endpoint_id: str):
    from ml.lstm import MIN_READINGS
    from ml.trainer import train_model

    db: Session = SessionLocal()
    try:
        recent = get_recent_readings(db, endpoint_id, limit=2000)
        latencies = [r.latency_ms for r in reversed(recent) if r.latency_ms is not None]
        if len(latencies) < MIN_READINGS:
            return
        model_path, scaler_path = train_model(endpoint_id, latencies)
        update_model_info(db, endpoint_id, model_path, scaler_path, len(latencies))
        logger.info(f"Initial model trained for endpoint {endpoint_id}")
    except Exception as e:
        logger.error(f"Background training failed for {endpoint_id}: {e}")
    finally:
        db.close()


def schedule_endpoint(endpoint_id: str, url: str, name: str, check_interval: int, alert_threshold: int, webhook_url: Optional[str], workspace_id: str = "demo"):
    job_id = f"monitor_{endpoint_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        check_endpoint,
        "interval",
        seconds=check_interval,
        id=job_id,
        args=[endpoint_id, url, name, alert_threshold, webhook_url, workspace_id],
        max_instances=1,
        coalesce=True,
    )


def unschedule_endpoint(endpoint_id: str):
    job_id = f"monitor_{endpoint_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
