import pytest
import respx
from httpx import Response
from app.infrastructure.webhook_delivery import enqueue_webhook, process_outbox_batch
from app.infrastructure.db import SessionLocal
from sqlalchemy import select
from app.infrastructure.outbox import OutboxWebhook


@pytest.mark.asyncio
async def test_webhook_delivery_retry(client):
    target = "http://client.test/hook"
    await enqueue_webhook(target, {"hello": "world"})

    with respx.mock(assert_all_called=False) as rs:
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            if calls["n"] < 5:
                return Response(500, json={"ok": False})
            return Response(200, json={"ok": True})

        rs.post(target).mock(side_effect=handler)

        for _ in range(5):
            await process_outbox_batch(None, limit=50)
            async with SessionLocal() as s:
                q = await s.execute(select(OutboxWebhook))
                items = q.scalars().all()
                for it in items:
                    it.next_attempt_at = it.next_attempt_at.replace(year=2000)
                await s.commit()

    async with SessionLocal() as s:
        q = await s.execute(select(OutboxWebhook))
        items = q.scalars().all()
        assert len(items) == 0
