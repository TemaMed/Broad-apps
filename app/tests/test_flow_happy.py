import pytest
from app.tests.dummy_provider import DummyProvider, DummyProviderState
from app.application.ports.provider import ProviderResult
from app.workers import tasks as worker_tasks


@pytest.mark.asyncio
async def test_happy_flow_register_topup_generate_success(client, monkeypatch):
    r = await client.post("/auth/register", json={"external_user_id": "u-happy"})
    assert r.status_code == 200
    api_key = r.json()["api_key"]

    r = await client.post(
        "/payments/webhook",
        headers={"X-Webhook-Secret": "payments-secret"},
        json={"external_user_id": "u-happy", "amount": 100},
    )
    assert r.status_code == 200

    r = await client.post(
        "/generations/images",
        headers={"X-API-Key": api_key},
        json={"prompt": "test prompt"},
    )
    assert r.status_code == 200
    gen_id = r.json()["generation_id"]

    bal = await client.get("/users/me/balance", headers={"X-API-Key": api_key})
    b = bal.json()
    assert b["balance_tokens"] == 100
    assert b["reserved_tokens"] == 10  # image cost by pricing.py
    assert b["available_tokens"] == 90

    state = DummyProviderState(statuses={})
    dummy = DummyProvider(state)

    def _provider():
        return dummy

    monkeypatch.setattr(worker_tasks, "_provider", _provider)

    await worker_tasks.submit_generation(None, gen_id, "http://api:8000")

    g = await client.get(f"/generations/{gen_id}", headers={"X-API-Key": api_key})
    assert g.status_code == 200
    assert g.json()["status"] in ("queued", "created")
    rid = "req-1"
    state.statuses[rid] = ProviderResult(status="completed", result_url="https://example.com/img.png")

    await worker_tasks.poll_generation(None, gen_id)

    g2 = await client.get(f"/generations/{gen_id}", headers={"X-API-Key": api_key})
    assert g2.json()["status"] == "completed"
    assert g2.json()["result_url"] == "https://example.com/img.png"

    bal2 = await client.get("/users/me/balance", headers={"X-API-Key": api_key})
    b2 = bal2.json()
    assert b2["reserved_tokens"] == 0
    assert b2["balance_tokens"] == 90  # spent 10
