from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user import User
from app.domain.wallet import Wallet
from app.domain.generation import Generation
from app.domain.enums import GenerationKind, GenerationStatus

from app.application.ports.repositories import UserRepository, GenerationRepository
from app.infrastructure.models import UserModel, GenerationModel

class SqlUserRepo(UserRepository):
    def __init__(self, s: AsyncSession):
        self.s = s

    async def get(self, user_id: UUID) -> User | None:
        row = await self.s.get(UserModel, user_id)
        return self._to_domain(row) if row else None

    async def get_by_external_id(self, external_user_id: str) -> User | None:
        q = await self.s.execute(select(UserModel).where(UserModel.external_user_id == external_user_id))
        row = q.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_api_key_hash(self, api_key_hash: str) -> User | None:
        q = await self.s.execute(select(UserModel).where(UserModel.api_key_hash == api_key_hash))
        row = q.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def add(self, user: User) -> None:
        w = user.ensure_wallet()
        self.s.add(UserModel(
            id=user.id,
            external_user_id=user.external_user_id,
            api_key_hash=user.api_key_hash,
            balance_tokens=w.balance_tokens,
            reserved_tokens=w.reserved_tokens,
        ))

    async def save(self, user: User) -> None:
        row = await self.s.get(UserModel, user.id)
        if not row:
            await self.add(user)
            return
        w = user.ensure_wallet()
        row.external_user_id = user.external_user_id
        row.api_key_hash = user.api_key_hash
        row.balance_tokens = w.balance_tokens
        row.reserved_tokens = w.reserved_tokens

    def _to_domain(self, row: UserModel) -> User:
        u = User(id=row.id, external_user_id=row.external_user_id, api_key_hash=row.api_key_hash)
        u.wallet = Wallet(user_id=row.id, balance_tokens=row.balance_tokens, reserved_tokens=row.reserved_tokens)
        return u

class SqlGenerationRepo(GenerationRepository):
    def __init__(self, s: AsyncSession):
        self.s = s

    async def get(self, generation_id: UUID) -> Generation | None:
        row = await self.s.get(GenerationModel, generation_id)
        return self._to_domain(row) if row else None

    async def get_by_provider_request_id(self, provider_request_id: str) -> Generation | None:
        q = await self.s.execute(select(GenerationModel).where(GenerationModel.provider_request_id == provider_request_id))
        row = q.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def add(self, gen: Generation) -> None:
        self.s.add(GenerationModel(
            id=gen.id, user_id=gen.user_id,
            kind=gen.kind.value, status=gen.status.value,
            prompt=gen.prompt, input_image_url=gen.input_image_url,
            provider=gen.provider, provider_request_id=gen.provider_request_id,
            cost_tokens=gen.cost_tokens,
            result_url=gen.result_url, error=gen.error,
            callback_url=gen.callback_url,
            created_at=gen.created_at, updated_at=gen.updated_at,
        ))

    async def save(self, gen: Generation) -> None:
        row = await self.s.get(GenerationModel, gen.id)
        if not row:
            await self.add(gen)
            return
        row.status = gen.status.value
        row.provider_request_id = gen.provider_request_id
        row.result_url = gen.result_url
        row.error = gen.error
        row.updated_at = gen.updated_at

    def _to_domain(self, row: GenerationModel) -> Generation:
        return Generation(
            id=row.id, user_id=row.user_id,
            kind=GenerationKind(row.kind),
            status=GenerationStatus(row.status),
            prompt=row.prompt,
            input_image_url=row.input_image_url,
            provider=row.provider,
            provider_request_id=row.provider_request_id,
            cost_tokens=row.cost_tokens,
            result_url=row.result_url,
            error=row.error,
            callback_url=row.callback_url,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
