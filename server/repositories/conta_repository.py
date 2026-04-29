from decimal import Decimal

from server.models.conta import Conta, TipoConta


def _row_to_conta(row: dict) -> Conta:
    return Conta(
        id=row["id"],
        usuario_id=row["usuario_id"],
        numero_conta=row["numero_conta"],
        agencia=row["agencia"],
        saldo=row["saldo"] if isinstance(row["saldo"], Decimal) else Decimal(str(row["saldo"])),
        tipo_conta=TipoConta(row["tipo_conta"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class ContaRepository:
    DEFAULT_AGENCIA = "0001"

    @staticmethod
    def _normalize_agencia(value: str | None) -> str:
        raw = (value or ContaRepository.DEFAULT_AGENCIA).strip()
        if not raw.isdigit() or len(raw) != 4:
            raise ValueError("Agencia deve conter exatamente 4 digitos numericos.")
        return raw

    @staticmethod
    def _next_account_number(db) -> str:
        cursor = db.cursor()
        cursor.execute("SELECT MAX(CAST(numero_conta AS UNSIGNED)) FROM contas")
        current_max = cursor.fetchone()[0]
        cursor.close()
        next_number = (current_max or 0) + 1
        return f"{next_number:010d}"

    @classmethod
    def create(
        cls,
        db,
        *,
        usuario_id: int,
        tipo_conta: TipoConta = TipoConta.CHECKING,
        agencia: str | None = None,
    ) -> Conta:
        numero_conta = cls._next_account_number(db)
        agencia_norm = cls._normalize_agencia(agencia)

        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO contas (usuario_id, numero_conta, agencia, saldo, tipo_conta)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (usuario_id, numero_conta, agencia_norm, Decimal("0.00"), tipo_conta.value),
        )
        new_id = cursor.lastrowid
        cursor.close()

        return cls.get_by_id(db, new_id)

    @classmethod
    def get_by_id(cls, db, conta_id: int) -> Conta | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM contas WHERE id = %s", (conta_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_conta(row) if row else None

    @classmethod
    def get_by_usuario_id(cls, db, usuario_id: int) -> list[Conta]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM contas WHERE usuario_id = %s", (usuario_id,))
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_conta(row) for row in rows]

    @classmethod
    def get_by_numero_conta(cls, db, numero_conta: str) -> Conta | None:
        normalized = "".join(ch for ch in numero_conta if ch.isdigit())
        if not normalized:
            return None
        normalized = normalized.zfill(10)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM contas WHERE numero_conta = %s", (normalized,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_conta(row) if row else None

    @classmethod
    def count_all(cls, db) -> int:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM contas")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    @classmethod
    def get_grouped_by_usuario_ids(
        cls,
        db,
        usuario_ids: list[int],
    ) -> dict[int, list[Conta]]:
        if not usuario_ids:
            return {}

        placeholders = ", ".join(["%s"] * len(usuario_ids))
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM contas WHERE usuario_id IN ({placeholders}) "
            "ORDER BY usuario_id ASC, id ASC",
            usuario_ids,
        )
        rows = cursor.fetchall()
        cursor.close()

        grouped: dict[int, list[Conta]] = {uid: [] for uid in usuario_ids}
        for row in rows:
            conta = _row_to_conta(row)
            grouped.setdefault(conta.usuario_id, []).append(conta)

        return grouped
