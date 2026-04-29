from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Investimento:
    id: int
    usuario_id: int
    tipo_investimento: str
    nome_ativo: str
    valor_aplicado: Decimal
    rentabilidade: Decimal | None
    data_aplicacao: datetime
    created_at: datetime
    updated_at: datetime
