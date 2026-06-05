import random
from decimal import Decimal

from server.models.credit_card import (
    CreditCard,
    CreditCardStatus,
    CreditCardTransaction,
    CreditCardTransactionType,
)


def _row_to_card(row: dict) -> CreditCard:
    return CreditCard(
        id=row["id"],
        user_id=row["user_id"],
        card_number=row["card_number"],
        card_name=row["card_name"],
        limit_amount=row["limit_amount"] if isinstance(row["limit_amount"], Decimal) else Decimal(str(row["limit_amount"])),
        used_amount=row["used_amount"] if isinstance(row["used_amount"], Decimal) else Decimal(str(row["used_amount"])),
        due_day=row["due_day"],
        status=CreditCardStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_tx(row: dict) -> CreditCardTransaction:
    return CreditCardTransaction(
        id=row["id"],
        credit_card_id=row["credit_card_id"],
        type=CreditCardTransactionType(row["type"]),
        amount=row["amount"] if isinstance(row["amount"], Decimal) else Decimal(str(row["amount"])),
        description=row["description"],
        created_at=row["created_at"],
    )


class CreditCardRepository:
    @classmethod
    def _generate_card_number(cls, db) -> str:
        while True:
            number = "4" + "".join([str(random.randint(0, 9)) for _ in range(15)])
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM credit_cards WHERE card_number = %s", (number,))
            count = cursor.fetchone()[0]
            cursor.close()
            if count == 0:
                return number

    @classmethod
    def get_by_id(cls, db, card_id: int) -> CreditCard | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_cards WHERE id = %s", (card_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_card(row) if row else None

    @classmethod
    def get_by_user_id(cls, db, user_id: int) -> CreditCard | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_cards WHERE user_id = %s LIMIT 1", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_card(row) if row else None

    @classmethod
    def create(
        cls,
        db,
        *,
        user_id: int,
        card_name: str,
        limit_amount: Decimal = Decimal("5000.00"),
        due_day: int = 10,
    ) -> CreditCard:
        card_number = cls._generate_card_number(db)
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO credit_cards (user_id, card_number, card_name, limit_amount, due_day) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, card_number, card_name, limit_amount, due_day),
        )
        new_id = cursor.lastrowid
        cursor.close()
        return cls.get_by_id(db, new_id)

    @classmethod
    def apply_purchase(cls, db, *, card_id: int, amount: Decimal) -> None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE credit_cards SET used_amount = used_amount + %s WHERE id = %s",
            (amount, card_id),
        )
        cursor.close()

    @classmethod
    def apply_payment(cls, db, *, card_id: int, amount: Decimal) -> None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE credit_cards SET used_amount = GREATEST(0, used_amount - %s) WHERE id = %s",
            (amount, card_id),
        )
        cursor.close()

    @classmethod
    def get_transactions(cls, db, card_id: int) -> list[CreditCardTransaction]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM credit_card_transactions WHERE credit_card_id = %s ORDER BY created_at DESC",
            (card_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_tx(row) for row in rows]

    @classmethod
    def create_transaction(
        cls,
        db,
        *,
        credit_card_id: int,
        type: CreditCardTransactionType,
        amount: Decimal,
        description: str | None = None,
    ) -> CreditCardTransaction:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO credit_card_transactions (credit_card_id, type, amount, description) "
            "VALUES (%s, %s, %s, %s)",
            (credit_card_id, type.value, amount, description),
        )
        new_id = cursor.lastrowid
        cursor.close()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_card_transactions WHERE id = %s", (new_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_tx(row)

    @classmethod
    def list_all(cls, db) -> list[CreditCard]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM credit_cards ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_card(row) for row in rows]

    @classmethod
    def update_limit(cls, db, *, card_id: int, new_limit: Decimal) -> None:
        cursor = db.cursor()
        cursor.execute("UPDATE credit_cards SET limit_amount = %s WHERE id = %s", (new_limit, card_id))
        cursor.close()

    @classmethod
    def delete(cls, db, *, card_id: int) -> None:
        cursor = db.cursor()
        cursor.execute("DELETE FROM credit_cards WHERE id = %s", (card_id,))
        cursor.close()
