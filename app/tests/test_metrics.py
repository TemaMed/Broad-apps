import pytest


@pytest.mark.asyncio
async def test_metrics_has_api_requests(client):
    await client.get("/metrics")
    await client.get("/metrics")

    r = await client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "api_requests_total" in body
