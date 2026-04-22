from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from server.models.orm_models import Conta, TipoConta


class ContaRepository:
    DEFAULT_AGENCIA = "0001"

    @staticmethod
    def _normalize_agencia(value: str | None) -> str:
        raw = (value or ContaRepository.DEFAULT_AGENCIA).strip()
        if not raw.isdigit() or len(raw) != 4:
            raise ValueError("Agencia deve conter exatamente 4 digitos numericos.")
        return raw

    @staticmethod
    def _next_account_number(db: Session) -> str:
        current_max = db.execute(
            select(func.max(cast(Conta.numero_conta, Integer)))
        ).scalar_one_or_none()
        next_number = (current_max or 0) + 1
        return f"{next_number:010d}"

    @classmethod
    def create(
        cls,
        db: Session,
        *,
        usuario_id: int,
        tipo_conta: TipoConta = TipoConta.CHECKING,
        agencia: str | None = None,
    ) -> Conta:
        conta = Conta(
            usuario_id=usuario_id,
            numero_conta=cls._next_account_number(db),
            agencia=cls._normalize_agencia(agencia),
            tipo_conta=tipo_conta,
        )
        db.add(conta)
        db.flush()
        return conta

    @classmethod
    def get_by_usuario_id(cls, db: Session, usuario_id: int) -> list[Conta]:
        return list(db.execute(select(Conta).where(Conta.usuario_id == usuario_id)).scalars().all())

    @classmethod
    def get_by_numero_conta(cls, db: Session, numero_conta: str) -> Conta | None:
        normalized = "".join(ch for ch in numero_conta if ch.isdigit())
        if not normalized:
            return None
        normalized = normalized.zfill(10)
        return db.execute(select(Conta).where(Conta.numero_conta == normalized)).scalar_one_or_none()
