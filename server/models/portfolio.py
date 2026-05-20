from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Portfolio:
    id: int
    name: str
    stock_code: str
    stock_name: str
    stock_price: Decimal
    created_at: datetime
    updated_at: datetime
