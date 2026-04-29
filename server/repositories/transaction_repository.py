from decimal import Decimal

from server.models.transaction import Transaction, TransactionType


def _row_to_transaction(row: dict) -> Transaction:
    return Transaction(
        id=row["id"],
        type=TransactionType(row["type"]),
        from_account_id=row["from_account_id"],
        to_account_id=row["to_account_id"],
        amount=row["amount"] if isinstance(row["amount"], Decimal) else Decimal(str(row["amount"])),
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class TransactionRepository:
    @classmethod
    def get_by_id(cls, db, transaction_id: int) -> Transaction | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transactions WHERE id = %s", (transaction_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_transaction(row) if row else None

    @classmethod
    def get_by_account_id(cls, db, account_id: int) -> list[Transaction]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM transactions "
            "WHERE from_account_id = %s OR to_account_id = %s "
            "ORDER BY created_at DESC",
            (account_id, account_id),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_transaction(row) for row in rows]

    @classmethod
    def create(
        cls,
        db,
        *,
        type: TransactionType,
        from_account_id: int | None,
        to_account_id: int | None,
        amount: Decimal,
        description: str | None = None,
    ) -> Transaction:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (type, from_account_id, to_account_id, amount, description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (type.value, from_account_id, to_account_id, amount, description),
        )
        new_id = cursor.lastrowid
        cursor.close()
        return cls.get_by_id(db, new_id)
