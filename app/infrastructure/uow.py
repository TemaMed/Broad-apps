from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.db import SessionLocal
from app.infrastructure.repos import SqlUserRepo, SqlGenerationRepo

class SqlAlchemyUoW(UnitOfWork):
    def __init__(self):
        self.session = None
        self.users = None
        self.generations = None

    async def __aenter__(self):
        self.session = SessionLocal()
        self.users = SqlUserRepo(self.session)
        self.generations = SqlGenerationRepo(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
