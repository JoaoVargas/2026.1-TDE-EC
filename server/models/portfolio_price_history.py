from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class PortfolioPriceHistory:
    id: int
    portfolio_id: int
    price: Decimal
    recorded_at: datetime
