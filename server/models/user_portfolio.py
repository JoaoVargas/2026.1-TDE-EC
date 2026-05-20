from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class UserPortfolio:
    id: int
    portfolio_id: int
    user_id: int
    stock_amount: Decimal
    created_at: datetime
    updated_at: datetime
