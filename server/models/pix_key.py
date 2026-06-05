from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PixKeyType(str, Enum):
    CPF = "cpf"
    EMAIL = "email"
    PHONE = "phone"
    RANDOM = "random"


_LABELS = {
    PixKeyType.CPF: "CPF",
    PixKeyType.EMAIL: "E-mail",
    PixKeyType.PHONE: "Telefone",
    PixKeyType.RANDOM: "Chave aleatória",
}


@dataclass
class PixKey:
    id: int
    user_id: int
    account_id: int
    key_type: PixKeyType
    key_value: str
    created_at: datetime

    @property
    def type_label(self) -> str:
        return _LABELS.get(self.key_type, self.key_type.value)
