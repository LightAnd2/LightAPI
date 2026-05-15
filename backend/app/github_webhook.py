"""
GitHub webhook integration.
Receives push/deployment events, links them to monitored endpoints,
and runs a post-deploy regression analysis after a 10-minute observation window.
"""
import asyncio
import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session

from db.models import SessionLocal
from db.deploy_models import DeployEvent
from db.queries import get_all_endpoints, get_readings
from app.websocket import manager

logger = logging.getLogger(__name__)
router = APIRouter()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
POST_DEPLOY_WINDOW_SECONDS = 600
REGRESSION_THRESHOLD = 0.20


def _verify_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return True
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def _find_matching_endpoint(db: Session, repo_name: str, pusher: str) -> Optional[str]:
    endpoints = get_all_endpoints(db)
    repo_lower = repo_name.lower()
    for ep in endpoints:
        if repo_lower in ep.name.lower() or repo_lower in ep.url.lower():
            return ep.id
    for ep in endpoints:
        name_parts = ep.name.lower().replace("-", " ").replace("_", " ").split()
        repo_parts = repo_lower.replace("-", " ").replace("_", " ").split()
        if any(p in repo_parts for p in name_parts):
            return ep.id
    return None


def _compute_baseline(db: Session, endpoint_id: str, since: datetime, until: datetime) -> Optional[float]:
    readings = get_readings(db, endpoint_id, "24h")
    window = [r.latency_ms for r in readings if r.latency_ms and since <= r.timestamp <= until and r.success]
    if len(window) < 3:
        return None
    return round(sum(window) / len(window), 2)


async def _run_post_deploy_analysis(deploy_id: str, endpoint_id: str, deployed_at: datetime, pre_baseline: Optional[float]):
    await asyncio.sleep(POST_DEPLOY_WINDOW_SECONDS)

    db: Session = SessionLocal()
    try:
        deploy = db.query(DeployEvent).filter(DeployEvent.id == deploy_id).first()
        if not deploy:
            return

        window_start = deployed_at
        window_end = deployed_at + timedelta(seconds=POST_DEPLOY_WINDOW_SECONDS)
        post_baseline = _compute_baseline(db, endpoint_id, window_start, window_end)

        regression_detected = False
        regression_percent = None

        if pre_baseline and post_baseline:
            change = (post_baseline - pre_baseline) / pre_baseline
            regression_detected = change > REGRESSION_THRESHOLD
            regression_percent = round(change * 100, 1)

        deploy.post_deploy_baseline_ms = post_baseline
        deploy.regression_detected = regression_detected
        deploy.regression_percent = regression_percent
        deploy.analysis_complete = True
        db.commit()

        message = {
            "type": "deploy_analysis",
            "endpoint_id": endpoint_id,
            "data": {
                "deploy_id": deploy_id,
                "commit_sha": deploy.commit_sha[:7],
                "commit_message": deploy.commit_message,
                "pusher": deploy.pusher,
                "pre_deploy_ms": pre_baseline,
                "post_deploy_ms": post_baseline,
                "regression_detected": regression_detected,
                "regression_percent": regression_percent,
                "verdict": (
                    f"Regression detected: latency increased {regression_percent}% after commit {deploy.commit_sha[:7]}"
                    if regression_detected
                    else f"No regression. Latency stable after deploy ({deploy.commit_sha[:7]})"
                ),
            },
        }
        await manager.broadcast(message, endpoint_id)
        logger.info(f"Deploy analysis complete for {deploy_id}: regression={regression_detected}")

    except Exception as e:
        logger.error(f"Post-deploy analysis failed for {deploy_id}: {e}")
    finally:
        db.close()


@router.post("/api/webhooks/github")
async def github_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if WEBHOOK_SECRET and not _verify_signature(body, sig):
        raise HTTPException(401, "Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event not in ("push", "deployment", "ping"):
        return {"status": "ignored", "event": event}

    if event == "ping":
        return {"status": "pong"}

    payload = await request.json()
    repo = payload.get("repository", {}).get("name", "unknown")
    branch = (payload.get("ref", "") or "").replace("refs/heads/", "")
    commit_sha = payload.get("after") or payload.get("deployment", {}).get("sha", "")
    commit_message = (
        payload.get("head_commit", {}) or {}
    ).get("message", "")
    pusher = (payload.get("pusher", {}) or {}).get("name", "")

    if not commit_sha or commit_sha == "0000000000000000000000000000000000000000":
        return {"status": "ignored", "reason": "branch deletion"}

    deploy_id = str(uuid.uuid4())
    deployed_at = datetime.utcnow()

    db: Session = SessionLocal()
    try:
        endpoint_id = _find_matching_endpoint(db, repo, pusher)

        pre_baseline = None
        if endpoint_id:
            window_end = deployed_at
            window_start = deployed_at - timedelta(hours=1)
            pre_baseline = _compute_baseline(db, endpoint_id, window_start, window_end)

        event_record = DeployEvent(
            id=deploy_id,
            endpoint_id=endpoint_id,
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            commit_message=commit_message[:200] if commit_message else None,
            pusher=pusher,
            deployed_at=deployed_at,
            pre_deploy_baseline_ms=pre_baseline,
        )
        db.add(event_record)
        db.commit()

        logger.info(f"Deploy event received: {repo}@{commit_sha[:7]} → endpoint={endpoint_id}")

        if endpoint_id:
            asyncio.create_task(_run_post_deploy_analysis(deploy_id, endpoint_id, deployed_at, pre_baseline))
            await manager.broadcast({
                "type": "deploy_started",
                "endpoint_id": endpoint_id,
                "data": {
                    "deploy_id": deploy_id,
                    "repo": repo,
                    "branch": branch,
                    "commit_sha": commit_sha[:7],
                    "commit_message": commit_message,
                    "pusher": pusher,
                    "pre_deploy_baseline_ms": pre_baseline,
                    "message": f"Deploy detected — monitoring for regressions for 10 minutes",
                },
            }, endpoint_id)

    finally:
        db.close()

    return {
        "status": "accepted",
        "deploy_id": deploy_id,
        "endpoint_matched": endpoint_id is not None,
        "monitoring": endpoint_id is not None,
    }


@router.get("/api/endpoints/{endpoint_id}/deploys")
def get_deploys(endpoint_id: str):
    db: Session = SessionLocal()
    try:
        deploys = (
            db.query(DeployEvent)
            .filter(DeployEvent.endpoint_id == endpoint_id)
            .order_by(DeployEvent.deployed_at.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "id": d.id,
                "repo": d.repo,
                "branch": d.branch,
                "commit_sha": d.commit_sha[:7],
                "commit_message": d.commit_message,
                "pusher": d.pusher,
                "deployed_at": d.deployed_at.isoformat(),
                "pre_deploy_baseline_ms": d.pre_deploy_baseline_ms,
                "post_deploy_baseline_ms": d.post_deploy_baseline_ms,
                "regression_detected": d.regression_detected,
                "regression_percent": d.regression_percent,
                "analysis_complete": d.analysis_complete,
            }
            for d in deploys
        ]
    finally:
        db.close()
