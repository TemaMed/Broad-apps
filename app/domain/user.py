from dataclasses import dataclass
from .base import AggregateRoot
from .wallet import Wallet

@dataclass
class User(AggregateRoot):
    external_user_id: str = ""
    api_key_hash: str = ""
    wallet: Wallet | None = None

    def ensure_wallet(self) -> Wallet:
        if self.wallet is None:
            self.wallet = Wallet(user_id=self.id)
        return self.wallet
