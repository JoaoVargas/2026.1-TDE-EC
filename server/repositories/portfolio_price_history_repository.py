from decimal import Decimal

from server.models.portfolio_price_history import PortfolioPriceHistory


def _row_to_history(row: dict) -> PortfolioPriceHistory:
    return PortfolioPriceHistory(
        id=row["id"],
        portfolio_id=row["portfolio_id"],
        price=row["price"] if isinstance(row["price"], Decimal) else Decimal(str(row["price"])),
        recorded_at=row["recorded_at"],
    )


class PortfolioPriceHistoryRepository:
    @classmethod
    def record(cls, db, *, portfolio_id: int, price: Decimal) -> PortfolioPriceHistory:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO portfolio_price_history (portfolio_id, price) VALUES (%s, %s)",
            (portfolio_id, price),
        )
        new_id = cursor.lastrowid
        cursor.close()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM portfolio_price_history WHERE id = %s", (new_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_history(row)

    @classmethod
    def get_by_portfolio_id(cls, db, portfolio_id: int, limit: int = 60) -> list[PortfolioPriceHistory]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM portfolio_price_history WHERE portfolio_id = %s "
            "ORDER BY recorded_at DESC LIMIT %s",
            (portfolio_id, limit),
        )
        rows = cursor.fetchall()
        cursor.close()
        # Return chronological order (oldest first) for chart rendering
        return list(reversed([_row_to_history(row) for row in rows]))

    @classmethod
    def get_latest(cls, db, portfolio_id: int) -> PortfolioPriceHistory | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM portfolio_price_history WHERE portfolio_id = %s "
            "ORDER BY recorded_at DESC LIMIT 1",
            (portfolio_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return _row_to_history(row) if row else None
