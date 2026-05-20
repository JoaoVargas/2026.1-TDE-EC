from decimal import Decimal

from server.models.user_portfolio import UserPortfolio


def _row_to_user_portfolio(row: dict) -> UserPortfolio:
    return UserPortfolio(
        id=row["id"],
        portfolio_id=row["portfolio_id"],
        user_id=row["user_id"],
        stock_amount=row["stock_amount"] if isinstance(row["stock_amount"], Decimal) else Decimal(str(row["stock_amount"])),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class UserPortfolioRepository:
    @classmethod
    def get_by_user_id(cls, db, user_id: int) -> list[UserPortfolio]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM user_portfolios WHERE user_id = %s",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_user_portfolio(row) for row in rows]

    @classmethod
    def create(
        cls,
        db,
        *,
        portfolio_id: int,
        user_id: int,
        stock_amount: Decimal,
    ) -> UserPortfolio:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO user_portfolios (portfolio_id, user_id, stock_amount) VALUES (%s, %s, %s)",
            (portfolio_id, user_id, stock_amount),
        )
        new_id = cursor.lastrowid
        cursor.close()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_portfolios WHERE id = %s", (new_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user_portfolio(row)

    @classmethod
    def get_by_user_and_portfolio(cls, db, user_id: int, portfolio_id: int) -> UserPortfolio | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM user_portfolios WHERE user_id = %s AND portfolio_id = %s",
            (user_id, portfolio_id),
        )
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user_portfolio(row) if row else None

    @classmethod
    def update_amount(cls, db, *, user_portfolio_id: int, stock_amount: Decimal) -> UserPortfolio | None:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE user_portfolios SET stock_amount = %s WHERE id = %s",
            (stock_amount, user_portfolio_id),
        )
        cursor.close()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_portfolios WHERE id = %s", (user_portfolio_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_user_portfolio(row) if row else None

    @classmethod
    def get_by_portfolio_id(cls, db, portfolio_id: int) -> list["UserPortfolio"]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM user_portfolios WHERE portfolio_id = %s",
            (portfolio_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_user_portfolio(row) for row in rows]

    @classmethod
    def delete(cls, db, *, user_portfolio_id: int) -> bool:
        cursor = db.cursor()
        cursor.execute("DELETE FROM user_portfolios WHERE id = %s", (user_portfolio_id,))
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    @classmethod
    def delete_by_portfolio_id(cls, db, *, portfolio_id: int) -> int:
        cursor = db.cursor()
        cursor.execute("DELETE FROM user_portfolios WHERE portfolio_id = %s", (portfolio_id,))
        affected = cursor.rowcount
        cursor.close()
        return affected
