from abc import ABC, abstractmethod
from app.application.ports.repositories import UserRepository, GenerationRepository

class UnitOfWork(ABC):
    users: UserRepository
    generations: GenerationRepository

    @abstractmethod
    async def __aenter__(self): ...
    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb): ...
    @abstractmethod
    async def commit(self) -> None: ...
    @abstractmethod
    async def rollback(self) -> None: ...
