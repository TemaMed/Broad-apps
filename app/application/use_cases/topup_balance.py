from dataclasses import dataclass
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.user import User

@dataclass(frozen=True)
class TopUpCmd:
    external_user_id: str
    amount: int

async def topup_balance(uow: UnitOfWork, cmd: TopUpCmd) -> None:
    async with uow:
        user = await uow.users.get_by_external_id(cmd.external_user_id)
        if not user:
            user = User(external_user_id=cmd.external_user_id, api_key_hash="")
            user.ensure_wallet()
            await uow.users.add(user)
        wallet = user.ensure_wallet()
        wallet.topup(cmd.amount)
        await uow.users.save(user)
        await uow.commit()
