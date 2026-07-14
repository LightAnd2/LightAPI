"""
Baseline drift detection — compares recent latency baseline against historical
baseline to detect silent performance degradation over days/weeks.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from db.queries import get_readings


DRIFT_THRESHOLD = 0.30
SIGNIFICANT_DRIFT = 0.75
MIN_READINGS = 20


def compute_baseline(readings) -> Optional[float]:
    latencies = [r.latency_ms for r in readings if r.latency_ms is not None and r.success]
    if len(latencies) < MIN_READINGS:
        return None
    return sum(latencies) / len(latencies)


def detect_drift(db: Session, endpoint_id: str) -> Optional[dict]:
    readings_30d = get_readings(db, endpoint_id, "30d")
    readings_7d = get_readings(db, endpoint_id, "7d")
    readings_24h = get_readings(db, endpoint_id, "24h")

    baseline_30d = compute_baseline(readings_30d)
    baseline_7d = compute_baseline(readings_7d)
    baseline_24h = compute_baseline(readings_24h)

    if baseline_30d is None or baseline_24h is None:
        return None

    drift_ratio = (baseline_24h - baseline_30d) / baseline_30d

    if abs(drift_ratio) < DRIFT_THRESHOLD:
        return {
            "status": "stable",
            "drift_percent": round(drift_ratio * 100, 1),
            "baseline_30d_ms": round(baseline_30d, 1),
            "baseline_7d_ms": round(baseline_7d, 1) if baseline_7d else None,
            "baseline_24h_ms": round(baseline_24h, 1),
            "message": "Latency is stable relative to 30-day baseline.",
        }

    direction = "degraded" if drift_ratio > 0 else "improved"
    severity = "critical" if abs(drift_ratio) >= SIGNIFICANT_DRIFT else "warning"

    if direction == "degraded":
        if severity == "critical":
            message = f"Latency has silently degraded {round(drift_ratio * 100)}% over the past 30 days ({round(baseline_30d)}ms → {round(baseline_24h)}ms). This service is significantly slower than its historical baseline."
        else:
            message = f"Latency has drifted up {round(drift_ratio * 100)}% from the 30-day baseline ({round(baseline_30d)}ms → {round(baseline_24h)}ms)."
    else:
        message = f"Latency has improved {round(abs(drift_ratio) * 100)}% from the 30-day baseline ({round(baseline_30d)}ms → {round(baseline_24h)}ms)."

    weekly_drift = None
    if baseline_7d and baseline_30d:
        weekly_drift = round(((baseline_24h - baseline_7d) / baseline_7d) * 100, 1) if baseline_7d > 0 else None

    return {
        "status": direction,
        "severity": severity,
        "drift_percent": round(drift_ratio * 100, 1),
        "weekly_drift_percent": weekly_drift,
        "baseline_30d_ms": round(baseline_30d, 1),
        "baseline_7d_ms": round(baseline_7d, 1) if baseline_7d else None,
        "baseline_24h_ms": round(baseline_24h, 1),
        "message": message,
    }


def check_all_drift(db: Session, workspace_id: str = "demo") -> list[dict]:
    from db.queries import get_all_endpoints
    results = []
    for ep in get_all_endpoints(db, workspace_id):
        drift = detect_drift(db, ep.id)
        if drift and drift["status"] != "stable":
            results.append({"endpoint_id": ep.id, "endpoint_name": ep.name, **drift})
    return results
