from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class TipoUsuario(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"


@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    senha: str
    data_nascimento: date
    cpf: str
    cep: str
    logradouro: str | None
    numero: str | None
    bairro: str | None
    cidade: str | None
    estado: str | None
    tipo_usuario: TipoUsuario
    created_at: datetime
    updated_at: datetime
