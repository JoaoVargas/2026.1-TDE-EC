from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    INTERNAL = "internal"
    TRANSACTION = "transaction"
    EXPENSE = "expense"
    OTHER = "other"


@dataclass
class Transaction:
    id: int
    type: TransactionType
    from_account_id: int | None
    to_account_id: int | None
    amount: Decimal
    description: str | None
    created_at: datetime
    updated_at: datetime
