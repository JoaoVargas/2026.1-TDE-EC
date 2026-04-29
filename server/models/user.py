from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class UserType(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"


@dataclass
class User:
    id: int
    cpf: str
    type: UserType
    name: str
    email: str
    password: str
    birthday: date
    address_id: int
    created_at: datetime
    updated_at: datetime
