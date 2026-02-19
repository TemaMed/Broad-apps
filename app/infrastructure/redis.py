# app/infrastructure/redis.py
from redis.asyncio import Redis
from app.settings import settings

redis_client = Redis.from_url(settings.redis_dsn, decode_responses=True)

def reinit_redis(dsn: str) -> None:
    global redis_client
    redis_client = Redis.from_url(dsn, decode_responses=True)
