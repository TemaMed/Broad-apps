import os
import importlib
import pathlib
import pytest
import pytest_asyncio
import httpx
from sqlalchemy import text


def _running_inside_docker() -> bool:
    return pathlib.Path("/.dockerenv").exists() or os.getenv("IN_DOCKER") == "1"


_PG_HOST = os.getenv("TEST_PG_HOST") or ("postgres" if _running_inside_docker() else "localhost")
_REDIS_HOST = os.getenv("TEST_REDIS_HOST") or ("redis" if _running_inside_docker() else "localhost")

os.environ.setdefault("POSTGRES_DSN", f"postgresql+asyncpg://gen:gen@{_PG_HOST}:5432/gen")
os.environ.setdefault("REDIS_DSN", f"redis://{_REDIS_HOST}:6379/0")

os.environ.setdefault("FAL_API_KEY_PRIMARY", "dummy")
os.environ.setdefault("PAYMENTS_WEBHOOK_SECRET", "payments-secret")
os.environ.setdefault("LOG_DIR", "/tmp")


@pytest.fixture(scope="session")
def migrated_schema():
    """
    Миграции один раз на сессию. Это sync-часть (alembic сам создаёт коннект).
    """
    import app.settings as settings_mod
    importlib.reload(settings_mod)

    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield


async def _truncate_all_tables(db_mod):
    """
    Чистим ВСЕ таблицы public schema, кроме alembic_version, через engine.
    Не зависит от того, как устроен async_sessionmaker.
    """
    engine = getattr(db_mod, "engine", None)
    if engine is None:
        raise RuntimeError("Не нашёл engine в app.infrastructure.db")

    async with engine.begin() as conn:
        res = await conn.execute(
            text(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename <> 'alembic_version';
                """
            )
        )
        tables = [r[0] for r in res.fetchall()]
        if tables:
            quoted = ", ".join(f'"{t}"' for t in tables)
            await conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE;"))


async def _flush_redis(rds_mod):
    client = getattr(rds_mod, "redis_client", None) or getattr(rds_mod, "client", None)
    if client is None:
        return
    try:
        await client.flushdb()
    except Exception:
        pass


async def _close_redis(rds_mod):
    client = getattr(rds_mod, "redis_client", None) or getattr(rds_mod, "client", None)
    if client is None:
        return

    close = getattr(client, "aclose", None) or getattr(client, "close", None)
    if close is not None:
        res = close()
        if hasattr(res, "__await__"):
            await res

    pool = getattr(client, "connection_pool", None)
    if pool is not None:
        disc = getattr(pool, "disconnect", None)
        if disc is not None:
            res = disc()
            if hasattr(res, "__await__"):
                await res


@pytest_asyncio.fixture
async def test_env(migrated_schema):
    """
    ВАЖНО: function-scope, чтобы каждый тест создавал db/redis в СВОЁМ event loop.
    Это убирает "Event loop is closed" на Windows.
    """
    import app.settings as settings_mod
    importlib.reload(settings_mod)

    import app.infrastructure.db as db
    importlib.reload(db)
    db.reinit_db(os.environ["POSTGRES_DSN"])

    import app.infrastructure.redis as rds
    importlib.reload(rds)
    rds.reinit_redis(os.environ["REDIS_DSN"])

    for mod_path in (
        "app.infrastructure.repos",
        "app.infrastructure.uow",
        "app.infrastructure.webhook_delivery",
        "app.infrastructure.rate_limit",
    ):
        try:
            m = importlib.import_module(mod_path)
            importlib.reload(m)
        except Exception:
            pass

    await _truncate_all_tables(db)
    await _flush_redis(rds)

    yield

    try:
        eng = getattr(db, "engine", None)
        if eng is not None:
            await eng.dispose()
    except Exception:
        pass

    try:
        await _close_redis(rds)
    except Exception:
        pass


@pytest_asyncio.fixture
async def client(test_env):
    from app.presentation.api import create_app

    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _disable_real_enqueue(monkeypatch):
    async def _noop_enqueue(*args, **kwargs):
        return None

    import app.presentation.routes_generations as rg
    monkeypatch.setattr(rg, "_enqueue", _noop_enqueue)
