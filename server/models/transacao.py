from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Transacao:
    id: int
    conta_id: int
    tipo_transacao: str
    descricao: str | None
    valor: Decimal
    data_transacao: datetime
    created_at: datetime
    updated_at: datetime
