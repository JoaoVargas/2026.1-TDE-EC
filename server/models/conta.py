from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TipoConta(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"


@dataclass
class Conta:
    id: int
    usuario_id: int
    numero_conta: str
    agencia: str
    saldo: Decimal
    tipo_conta: TipoConta
    created_at: datetime
    updated_at: datetime
