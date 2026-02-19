from dataclasses import dataclass
from uuid import UUID

@dataclass
class Wallet:
    user_id: UUID
    balance_tokens: int = 0
    reserved_tokens: int = 0

    def available(self) -> int:
        return self.balance_tokens - self.reserved_tokens

    def reserve(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        if self.available() < amount:
            raise ValueError("insufficient funds")
        self.reserved_tokens += amount

    def commit_spend(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        if self.reserved_tokens < amount:
            raise ValueError("not enough reserved")
        self.reserved_tokens -= amount
        self.balance_tokens -= amount

    def refund_reserved(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        if self.reserved_tokens < amount:
            raise ValueError("not enough reserved")
        self.reserved_tokens -= amount

    def topup(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        self.balance_tokens += amount
