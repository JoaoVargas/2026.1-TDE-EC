from decimal import Decimal

from server.models.portfolio import Portfolio


def _row_to_portfolio(row: dict) -> Portfolio:
    return Portfolio(
        id=row["id"],
        name=row["name"],
        stock_code=row["stock_code"],
        stock_name=row["stock_name"],
        stock_price=row["stock_price"] if isinstance(row["stock_price"], Decimal) else Decimal(str(row["stock_price"])),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PortfolioRepository:
    @classmethod
    def get_by_id(cls, db, portfolio_id: int) -> Portfolio | None:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM portfolios WHERE id = %s", (portfolio_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_portfolio(row) if row else None

    @classmethod
    def list_all(cls, db) -> list[Portfolio]:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM portfolios ORDER BY name ASC")
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_portfolio(row) for row in rows]

    @classmethod
    def create(
        cls,
        db,
        *,
        name: str,
        stock_code: str,
        stock_name: str,
        stock_price: Decimal,
    ) -> Portfolio:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO portfolios (name, stock_code, stock_name, stock_price)
            VALUES (%s, %s, %s, %s)
            """,
            (name, stock_code, stock_name, stock_price),
        )
        new_id = cursor.lastrowid
        cursor.close()
        return cls.get_by_id(db, new_id)
