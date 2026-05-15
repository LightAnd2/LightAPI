from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from db.models import Endpoint, Reading, Incident, AnomalyEvent, EndpointModel


RANGE_MAP = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
}


def get_all_endpoints(db: Session):
    return db.query(Endpoint).filter(Endpoint.is_active == True).all()


def get_endpoint(db: Session, endpoint_id: str) -> Optional[Endpoint]:
    return db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()


def create_endpoint(db: Session, url: str, name: str, check_interval: int, alert_threshold: int, webhook_url: Optional[str]) -> Endpoint:
    ep = Endpoint(url=url, name=name, check_interval=check_interval, alert_threshold=alert_threshold, webhook_url=webhook_url)
    db.add(ep)
    db.flush()
    model_info = EndpointModel(endpoint_id=ep.id)
    db.add(model_info)
    db.commit()
    db.refresh(ep)
    return ep


def delete_endpoint(db: Session, endpoint_id: str) -> bool:
    ep = get_endpoint(db, endpoint_id)
    if not ep:
        return False
    db.delete(ep)
    db.commit()
    return True


def save_reading(db: Session, endpoint_id: str, latency_ms: Optional[float], status_code: Optional[int], success: bool) -> Reading:
    r = Reading(endpoint_id=endpoint_id, timestamp=datetime.utcnow(), latency_ms=latency_ms, status_code=status_code, success=success)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_readings(db: Session, endpoint_id: str, range_str: str = "24h"):
    delta = RANGE_MAP.get(range_str, timedelta(hours=24))
    since = datetime.utcnow() - delta
    rows = (
        db.query(Reading)
        .filter(and_(Reading.endpoint_id == endpoint_id, Reading.timestamp >= since))
        .order_by(Reading.timestamp.asc())
        .all()
    )
    return rows


def get_recent_readings(db: Session, endpoint_id: str, limit: int = 100):
    return (
        db.query(Reading)
        .filter(Reading.endpoint_id == endpoint_id)
        .order_by(Reading.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_latest_reading(db: Session, endpoint_id: str) -> Optional[Reading]:
    return (
        db.query(Reading)
        .filter(Reading.endpoint_id == endpoint_id)
        .order_by(Reading.timestamp.desc())
        .first()
    )


def compute_uptime(db: Session, endpoint_id: str, days: int) -> float:
    since = datetime.utcnow() - timedelta(days=days)
    total = db.query(func.count(Reading.id)).filter(
        and_(Reading.endpoint_id == endpoint_id, Reading.timestamp >= since)
    ).scalar() or 0
    if total == 0:
        return 100.0
    successful = db.query(func.count(Reading.id)).filter(
        and_(Reading.endpoint_id == endpoint_id, Reading.timestamp >= since, Reading.success == True)
    ).scalar() or 0
    return round((successful / total) * 100, 2)


def get_incidents(db: Session, endpoint_id: str, limit: int = 20):
    return (
        db.query(Incident)
        .filter(Incident.endpoint_id == endpoint_id)
        .order_by(Incident.started_at.desc())
        .limit(limit)
        .all()
    )


def get_incidents_this_month(db: Session, endpoint_id: str) -> int:
    since = datetime.utcnow() - timedelta(days=30)
    return db.query(func.count(Incident.id)).filter(
        and_(Incident.endpoint_id == endpoint_id, Incident.started_at >= since)
    ).scalar() or 0


def get_open_incident(db: Session, endpoint_id: str) -> Optional[Incident]:
    return db.query(Incident).filter(
        and_(Incident.endpoint_id == endpoint_id, Incident.is_resolved == False)
    ).order_by(Incident.started_at.desc()).first()


def create_incident(db: Session, endpoint_id: str, severity: str = "warning") -> Incident:
    inc = Incident(endpoint_id=endpoint_id, severity=severity)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


def resolve_incident(db: Session, incident_id: str, peak_latency: Optional[float] = None):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc:
        inc.is_resolved = True
        inc.resolved_at = datetime.utcnow()
        if peak_latency:
            inc.peak_latency = peak_latency
        db.commit()


def update_incident_peak(db: Session, incident_id: str, latency: float):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if inc and (inc.peak_latency is None or latency > inc.peak_latency):
        inc.peak_latency = latency
        db.commit()


def save_anomaly(db: Session, endpoint_id: str, confidence: float, predicted: Optional[float], actual: float) -> AnomalyEvent:
    ev = AnomalyEvent(endpoint_id=endpoint_id, confidence=confidence, predicted_latency=predicted, actual_latency=actual)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def get_anomalies(db: Session, endpoint_id: str, limit: int = 20):
    return (
        db.query(AnomalyEvent)
        .filter(AnomalyEvent.endpoint_id == endpoint_id)
        .order_by(AnomalyEvent.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_model_info(db: Session, endpoint_id: str) -> Optional[EndpointModel]:
    return db.query(EndpointModel).filter(EndpointModel.endpoint_id == endpoint_id).first()


def update_model_info(db: Session, endpoint_id: str, model_path: str, scaler_path: str, readings_count: int):
    info = get_model_info(db, endpoint_id)
    if info:
        info.model_path = model_path
        info.scaler_path = scaler_path
        info.last_trained = datetime.utcnow()
        info.readings_count = readings_count
        info.is_ready = True
        db.commit()


def get_reading_count(db: Session, endpoint_id: str) -> int:
    return db.query(func.count(Reading.id)).filter(Reading.endpoint_id == endpoint_id).scalar() or 0


def get_global_stats(db: Session) -> dict:
    total = db.query(func.count(Endpoint.id)).filter(Endpoint.is_active == True).scalar() or 0
    active_incidents = db.query(func.count(Incident.id)).filter(Incident.is_resolved == False).scalar() or 0
    return {"total_endpoints": total, "active_incidents": active_incidents}
