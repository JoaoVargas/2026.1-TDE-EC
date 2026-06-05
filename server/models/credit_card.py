from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class CreditCardStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class CreditCardTransactionType(str, Enum):
    PURCHASE = "purchase"
    PAYMENT = "payment"


@dataclass
class CreditCard:
    id: int
    user_id: int
    card_number: str
    card_name: str
    limit_amount: Decimal
    used_amount: Decimal
    due_day: int
    status: CreditCardStatus
    created_at: datetime
    updated_at: datetime

    @property
    def available_amount(self) -> Decimal:
        return self.limit_amount - self.used_amount

    @property
    def masked_number(self) -> str:
        n = self.card_number
        if len(n) >= 16:
            return f"{n[:4]} **** **** {n[-4:]}"
        return n

    @property
    def formatted_number(self) -> str:
        n = self.card_number
        return " ".join(n[i:i+4] for i in range(0, len(n), 4)) if len(n) == 16 else n


@dataclass
class CreditCardTransaction:
    id: int
    credit_card_id: int
    type: CreditCardTransactionType
    amount: Decimal
    description: str | None
    created_at: datetime
