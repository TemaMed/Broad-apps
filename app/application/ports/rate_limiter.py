from abc import ABC, abstractmethod

class RateLimiter(ABC):
    @abstractmethod
    async def check(self, api_key: str) -> None: ...
