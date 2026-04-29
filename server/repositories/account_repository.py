from decimal import Decimal

from server.models.account import Account, AccountType


def _row_to_account(row: dict) -> Account:
    return Account(
        id=row["id"],
        user_id=row["user_id"],
        type=AccountType(row["type"]),
        account_number=row["account_number"],
        agency=row["agency"],
        balance=row["balance"] if isinstance(row["balance"], Decimal) else Decimal(str(row["balance"])),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class AccountRepository:
    DEFAULT_AGENCY = "0001"

    @staticmethod
    def _normalize_agency(value: str | None) -> str:
        raw = (value or AccountRepository.DEFAULT_AGENCY).strip()
        if not raw.isdigit() or len(raw) != 4:
            raise ValueError("Agency must contain exactly 4 numeric digits.")
        return raw

    @staticmethod
    def _next_account_number(db) -> str:
        cursor = db.cursor()
        cursor.execute("SELECT MAX(CAST(account_number AS UNSIGNED)) FROM accounts")
        current_max = cursor.fetchone()[0]
        cursor.close()
        next_number = (current_max or 0) + 1
        return f"{next_number:010d}"

    @classmethod
    def create(
        cls,
        db,
        *,
        user_id: int,
        type: AccountType = AccountType.CHECKING,
        agency: str | None = None,
    ) -> Account:
        account_number = cls._next_account_number(db)
        agency_norm = cls._normalize_agency(agency)

        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO accounts (user_id, type, account_number, agency, balance)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, type.value, account_number, agency_norm, Decimal("0.00")),
        )
        new_id = cursor.lastrowid
        cursor.close()

        return cls.get_by_id(db, new_id)

    @classmethod
    def get_by_id(cls, db, account_id: int) -> Account | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (account_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_account(row) if row else None

    @classmethod
    def get_by_user_id(cls, db, user_id: int) -> list[Account]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_account(row) for row in rows]

    @classmethod
    def get_by_account_number(cls, db, account_number: str) -> Account | None:
        normalized = "".join(ch for ch in account_number if ch.isdigit())
        if not normalized:
            return None
        normalized = normalized.zfill(10)
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (normalized,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_account(row) if row else None

    @classmethod
    def count_all(cls, db) -> int:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    @classmethod
    def get_grouped_by_user_ids(
        cls,
        db,
        user_ids: list[int],
    ) -> dict[int, list[Account]]:
        if not user_ids:
            return {}

        placeholders = ", ".join(["%s"] * len(user_ids))
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            f"SELECT * FROM accounts WHERE user_id IN ({placeholders}) "
            "ORDER BY user_id ASC, id ASC",
            user_ids,
        )
        rows = cursor.fetchall()
        cursor.close()

        grouped: dict[int, list[Account]] = {uid: [] for uid in user_ids}
        for row in rows:
            account = _row_to_account(row)
            grouped.setdefault(account.user_id, []).append(account)

        return grouped
