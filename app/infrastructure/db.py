from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncEngine

from app.settings import settings

engine: AsyncEngine = create_async_engine(settings.postgres_dsn, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

def reinit_db(dsn: str) -> None:
    global engine, SessionLocal
    engine = create_async_engine(dsn, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
