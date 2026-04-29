from dataclasses import dataclass
from datetime import datetime


@dataclass
class Address:
    id: int
    cep: str
    street: str
    state: str
    city: str
    neighborhood: str
    number: str
    created_at: datetime
    updated_at: datetime
