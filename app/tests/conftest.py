import os
import importlib
import pytest
import httpx


@pytest.fixture(scope="session")
def test_env():
    os.environ["POSTGRES_DSN"] = "postgresql+asyncpg://gen:gen@localhost:5432/gen"
    os.environ["REDIS_DSN"] = "redis://localhost:6379/0"

    os.environ["FAL_API_KEY_PRIMARY"] = "dummy"
    os.environ["PAYMENTS_WEBHOOK_SECRET"] = "payments-secret"
    os.environ["LOG_DIR"] = "/tmp"

    import app.settings as settings_mod
    importlib.reload(settings_mod)

    import app.infrastructure.db as db
    db.reinit_db(os.environ["POSTGRES_DSN"])

    import app.infrastructure.redis as rds
    rds.reinit_redis(os.environ["REDIS_DSN"])

    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    yield


@pytest.fixture
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
