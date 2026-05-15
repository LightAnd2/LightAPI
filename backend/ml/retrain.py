import logging
from sqlalchemy.orm import Session
from db.models import SessionLocal
from db.queries import get_all_endpoints, get_reading_count, get_recent_readings, get_model_info, update_model_info
from ml.lstm import MIN_READINGS
from ml.trainer import train_model

logger = logging.getLogger(__name__)


def retrain_all_endpoints():
    db: Session = SessionLocal()
    try:
        endpoints = get_all_endpoints(db)
        for ep in endpoints:
            count = get_reading_count(db, ep.id)
            if count < MIN_READINGS:
                continue
            try:
                readings = get_recent_readings(db, ep.id, limit=2000)
                latencies = [r.latency_ms for r in readings if r.latency_ms is not None]
                latencies.reverse()
                if len(latencies) < MIN_READINGS:
                    continue
                model_path, scaler_path = train_model(ep.id, latencies)
                update_model_info(db, ep.id, model_path, scaler_path, len(latencies))
                logger.info(f"Retrained model for endpoint {ep.id} ({ep.name}) with {len(latencies)} readings")
            except Exception as e:
                logger.error(f"Failed to retrain model for {ep.id}: {e}")
    finally:
        db.close()
