import pytest
from app.infrastructure.redis import redis_client


@pytest.mark.asyncio
async def test_rate_limit_and_ban(client):
    r = await client.post("/auth/register", json={"external_user_id": "u-rl"})
    api_key = r.json()["api_key"]
    headers = {"X-API-Key": api_key}

    for _ in range(10):
        rr = await client.get("/users/me/balance", headers=headers)
        assert rr.status_code in (200, 401, 402)

    rr = await client.get("/users/me/balance", headers=headers)
    assert rr.status_code in (429, 403)

    await redis_client.delete(f"ban:{api_key}")

    rr2 = await client.get("/users/me/balance", headers=headers)
    assert rr2.status_code in (200, 401, 402)
