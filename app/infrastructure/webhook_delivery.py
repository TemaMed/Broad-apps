import json
from datetime import datetime, timedelta
import httpx
from sqlalchemy import select
from app.settings import settings
from app.infrastructure.db import SessionLocal
from app.infrastructure.outbox import OutboxWebhook
from app.infrastructure.metrics import webhook_delivery_total

async def enqueue_webhook(target_url: str, payload: dict) -> None:
    async with SessionLocal() as s:
        s.add(OutboxWebhook(target_url=target_url, payload_json=json.dumps(payload)))
        await s.commit()

async def process_outbox_batch(ctx=None, limit: int = 50) -> None:
    now = datetime.utcnow()
    async with SessionLocal() as s:
        q = await s.execute(
            select(OutboxWebhook)
            .where(OutboxWebhook.next_attempt_at <= now)
            .order_by(OutboxWebhook.created_at.asc())
            .limit(limit)
        )
        items = q.scalars().all()

        async with httpx.AsyncClient(timeout=settings.http_timeout_s) as client:
            for item in items:
                if item.attempts >= settings.webhook_retry_attempts:
                    continue
                try:
                    r = await client.post(item.target_url, json=json.loads(item.payload_json))
                    if r.status_code >= 400:
                        raise RuntimeError(f"status={r.status_code}")
                    webhook_delivery_total.labels(status="ok").inc()
                    await s.delete(item)
                except Exception as e:
                    webhook_delivery_total.labels(status="error").inc()
                    item.attempts += 1
                    item.last_error = str(e)
                    item.next_attempt_at = datetime.utcnow() + timedelta(seconds=settings.webhook_retry_interval_s)
        await s.commit()
