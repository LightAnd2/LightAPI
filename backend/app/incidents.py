import logging
from typing import Optional
from sqlalchemy.orm import Session
from db.queries import get_open_incident, create_incident, resolve_incident, update_incident_peak

logger = logging.getLogger(__name__)


def handle_incident_lifecycle(db: Session, endpoint_id: str, success: bool, latency_ms: Optional[float], alert_threshold: int) -> dict:
    open_inc = get_open_incident(db, endpoint_id)
    result = {"opened": False, "resolved": False, "incident_id": None}

    if not success:
        if not open_inc:
            inc = create_incident(db, endpoint_id, severity="critical")
            result["opened"] = True
            result["incident_id"] = inc.id
            logger.info(f"Incident opened for endpoint {endpoint_id}")
        else:
            result["incident_id"] = open_inc.id
    elif latency_ms and latency_ms > alert_threshold:
        if not open_inc:
            inc = create_incident(db, endpoint_id, severity="warning")
            result["opened"] = True
            result["incident_id"] = inc.id
        else:
            result["incident_id"] = open_inc.id
            if latency_ms:
                update_incident_peak(db, open_inc.id, latency_ms)
    else:
        if open_inc:
            resolve_incident(db, open_inc.id, peak_latency=latency_ms)
            result["resolved"] = True
            result["incident_id"] = open_inc.id
            logger.info(f"Incident resolved for endpoint {endpoint_id}")

    return result
