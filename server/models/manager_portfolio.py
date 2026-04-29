from dataclasses import dataclass
from datetime import datetime


@dataclass
class ManagerPortfolio:
    id: int
    portfolio_id: int
    manager_id: int
    created_at: datetime
    updated_at: datetime
