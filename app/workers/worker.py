from urllib.parse import urlparse
from arq import cron
from arq.connections import RedisSettings
from app.infrastructure.webhook_delivery import process_outbox_batch
from app.settings import settings
from app.workers.tasks import submit_generation, poll_generation

def _redis_settings_from_dsn(dsn: str) -> RedisSettings:
    u = urlparse(dsn)
    db = int((u.path or "/0").lstrip("/"))
    return RedisSettings(host=u.hostname or "redis", port=u.port or 6379, database=db, password=u.password)

class WorkerSettings:
    redis_settings = _redis_settings_from_dsn(settings.redis_dsn)
    functions = [submit_generation, poll_generation]
    cron_jobs = [
        cron(process_outbox_batch, second={0, 15, 30, 45}),
    ]
