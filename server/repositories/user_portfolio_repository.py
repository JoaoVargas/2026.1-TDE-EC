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
