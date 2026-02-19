import hashlib
from fastapi import Header, HTTPException
from app.infrastructure.uow import SqlAlchemyUoW
from app.infrastructure.rate_limit import RedisRateLimiter
from app.application.common.errors import RateLimited, Banned

def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

async def auth_user(x_api_key: str = Header(..., alias="X-API-Key")):
    rl = RedisRateLimiter()
    try:
        await rl.check(x_api_key)
    except Banned as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))

    async with SqlAlchemyUoW() as uow:
        user = await uow.users.get_by_api_key_hash(_hash_api_key(x_api_key))
        if not user:
            raise HTTPException(status_code=401, detail="invalid api key")
        return user
