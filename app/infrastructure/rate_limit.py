from app.application.ports.rate_limiter import RateLimiter
from app.infrastructure.redis import redis_client
from app.settings import settings
from app.application.common.errors import RateLimited, Banned

class RedisRateLimiter(RateLimiter):
    async def check(self, api_key: str) -> None:
        ban_key = f"ban:{api_key}"
        if await redis_client.exists(ban_key):
            ttl = await redis_client.ttl(ban_key)
            raise Banned(f"banned for {ttl}s")

        key = f"rl:{api_key}"
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, 60)

        if count > settings.rate_limit_per_minute:
            await redis_client.setex(ban_key, settings.rate_limit_ban_seconds, "1")
            raise RateLimited("rate limit exceeded; banned for 60s")
