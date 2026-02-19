import pytest

@pytest.mark.asyncio
async def test_smoke_register(client):
    r = await client.post("/auth/register", json={"external_user_id": "u1"})
    assert r.status_code == 200
    assert "api_key" in r.json()
