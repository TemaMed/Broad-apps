import hashlib, secrets
from dataclasses import dataclass
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.user import User

@dataclass(frozen=True)
class RegisterUserCmd:
    external_user_id: str

@dataclass(frozen=True)
class RegisterUserRes:
    api_key: str

def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

async def register_user(uow: UnitOfWork, cmd: RegisterUserCmd) -> RegisterUserRes:
    async with uow:
        existing = await uow.users.get_by_external_id(cmd.external_user_id)
        api_key = secrets.token_urlsafe(32)
        if existing:
            existing.api_key_hash = _hash_api_key(api_key)
            existing.ensure_wallet()
            await uow.users.save(existing)
            await uow.commit()
            return RegisterUserRes(api_key=api_key)

        user = User(external_user_id=cmd.external_user_id, api_key_hash=_hash_api_key(api_key))
        user.ensure_wallet()
        await uow.users.add(user)
        await uow.commit()
        return RegisterUserRes(api_key=api_key)
