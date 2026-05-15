import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def fire_webhook(webhook_url: str, payload: dict):
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
    except Exception as e:
        logger.warning(f"Webhook delivery failed to {webhook_url}: {e}")


async def send_down_alert(endpoint_name: str, endpoint_url: str, webhook_url: Optional[str]):
    if not webhook_url:
        return
    await fire_webhook(webhook_url, {
        "type": "endpoint_down",
        "endpoint": endpoint_name,
        "url": endpoint_url,
        "message": f"{endpoint_name} is unreachable.",
    })


async def send_anomaly_alert(endpoint_name: str, endpoint_url: str, webhook_url: Optional[str], predicted_ms: Optional[float], actual_ms: float, confidence: float):
    if not webhook_url:
        return
    await fire_webhook(webhook_url, {
        "type": "anomaly_detected",
        "endpoint": endpoint_name,
        "url": endpoint_url,
        "actual_latency_ms": round(actual_ms, 1),
        "predicted_latency_ms": round(predicted_ms, 1) if predicted_ms else None,
        "confidence": confidence,
        "message": f"Anomaly detected on {endpoint_name}: {round(actual_ms)}ms latency (confidence {round(confidence*100)}%)",
    })


async def send_degradation_alert(endpoint_name: str, endpoint_url: str, webhook_url: Optional[str], predicted_ms: float, minutes_out: int = 15):
    if not webhook_url:
        return
    await fire_webhook(webhook_url, {
        "type": "degradation_predicted",
        "endpoint": endpoint_name,
        "url": endpoint_url,
        "predicted_latency_ms": round(predicted_ms, 1),
        "eta_minutes": minutes_out,
        "message": f"{endpoint_name} is degrading — predicted to exceed {round(predicted_ms)}ms in {minutes_out} minutes.",
    })
