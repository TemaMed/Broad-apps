import pytest
from app.tests.dummy_provider import DummyProvider, DummyProviderState
from app.application.ports.provider import ProviderResult
from app.workers import tasks as worker_tasks


@pytest.mark.asyncio
async def test_refund_on_failure(client, monkeypatch):
    r = await client.post("/auth/register", json={"external_user_id": "u-fail"})
    api_key = r.json()["api_key"]

    await client.post(
        "/payments/webhook",
        headers={"X-Webhook-Secret": "payments-secret"},
        json={"external_user_id": "u-fail", "amount": 100},
    )

    r = await client.post(
        "/generations/images",
        headers={"X-API-Key": api_key},
        json={"prompt": "will fail"},
    )
    gen_id = r.json()["generation_id"]

    bal = (await client.get("/users/me/balance", headers={"X-API-Key": api_key})).json()
    assert bal["reserved_tokens"] == 10

    state = DummyProviderState(statuses={})
    dummy = DummyProvider(state)

    def _provider():
        return dummy

    monkeypatch.setattr(worker_tasks, "_provider", _provider)

    await worker_tasks.submit_generation(None, gen_id, "http://api:8000")

    state.statuses["req-1"] = ProviderResult(status="failed", error="boom")

    await worker_tasks.poll_generation(None, gen_id)

    g = (await client.get(f"/generations/{gen_id}", headers={"X-API-Key": api_key})).json()
    assert g["status"] == "failed"
    assert "boom" in (g["error"] or "")

    bal2 = (await client.get("/users/me/balance", headers={"X-API-Key": api_key})).json()
    assert bal2["reserved_tokens"] == 0
    assert bal2["balance_tokens"] == 100
