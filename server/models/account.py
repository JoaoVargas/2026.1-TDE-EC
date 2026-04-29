from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"


@dataclass
class Account:
    id: int
    user_id: int
    type: AccountType
    account_number: str
    agency: str
    balance: Decimal
    created_at: datetime
    updated_at: datetime
