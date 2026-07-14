"""
Root cause analysis — when an endpoint goes down or degrades, cross-reference
all other monitored endpoints to determine if the failure is isolated or shared.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.queries import get_all_endpoints, get_readings, get_endpoint


CORRELATION_WINDOW_SECONDS = 120


def analyze_incident(db: Session, affected_endpoint_id: str, incident_time: datetime) -> dict:
    # Correlate only within the affected endpoint's workspace — never surface
    # other workspaces' endpoint names or URLs in the analysis.
    affected = get_endpoint(db, affected_endpoint_id)
    workspace_id = affected.workspace_id if affected else "demo"
    all_endpoints = get_all_endpoints(db, workspace_id)
    others = [ep for ep in all_endpoints if ep.id != affected_endpoint_id]

    window_start = incident_time - timedelta(seconds=CORRELATION_WINDOW_SECONDS)
    window_end = incident_time + timedelta(seconds=CORRELATION_WINDOW_SECONDS)

    correlated = []

    for ep in others:
        readings = get_readings(db, ep.id, "1h")
        window_readings = [
            r for r in readings
            if window_start <= r.timestamp <= window_end
        ]
        if not window_readings:
            continue

        failures = [r for r in window_readings if not r.success]
        high_latency = []

        if window_readings:
            recent_all = get_readings(db, ep.id, "24h")
            latencies = [r.latency_ms for r in recent_all if r.latency_ms is not None]
            if latencies:
                baseline = sum(latencies) / len(latencies)
                high_latency = [
                    r for r in window_readings
                    if r.latency_ms and r.latency_ms > baseline * 1.5
                ]

        if failures or high_latency:
            earliest = min(
                [r.timestamp for r in failures + high_latency],
                default=incident_time
            )
            offset_seconds = (earliest - incident_time).total_seconds()
            correlated.append({
                "endpoint_id": ep.id,
                "endpoint_name": ep.name,
                "endpoint_url": ep.url,
                "failures": len(failures),
                "high_latency_readings": len(high_latency),
                "offset_seconds": round(offset_seconds, 1),
            })

    if not correlated:
        return {
            "verdict": "isolated",
            "confidence": 0.85,
            "summary": "No other monitored endpoints were affected in the same window. Likely an application-level or endpoint-specific failure.",
            "correlated_endpoints": [],
        }

    upstream = [c for c in correlated if c["offset_seconds"] < -10]
    concurrent = [c for c in correlated if -10 <= c["offset_seconds"] <= 10]
    downstream = [c for c in correlated if c["offset_seconds"] > 10]

    if upstream:
        first = sorted(upstream, key=lambda x: x["offset_seconds"])[0]
        confidence = min(0.95, 0.6 + 0.1 * len(correlated))
        return {
            "verdict": "upstream_dependency",
            "confidence": round(confidence, 2),
            "summary": f"{first['endpoint_name']} degraded {abs(first['offset_seconds']):.0f}s before this incident — likely the root cause.",
            "correlated_endpoints": correlated,
        }
    elif concurrent:
        confidence = min(0.92, 0.55 + 0.12 * len(correlated))
        names = ", ".join(c["endpoint_name"] for c in concurrent[:3])
        return {
            "verdict": "shared_infrastructure",
            "confidence": round(confidence, 2),
            "summary": f"Multiple services failed simultaneously ({names}). Likely a shared infrastructure issue — network, database, or hosting layer.",
            "correlated_endpoints": correlated,
        }
    else:
        return {
            "verdict": "cascading_failure",
            "confidence": round(0.6 + 0.08 * len(downstream), 2),
            "summary": "This endpoint failed first. Downstream services were subsequently affected — this may be the origin of a cascading failure.",
            "correlated_endpoints": correlated,
        }
