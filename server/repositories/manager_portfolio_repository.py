from server.models.manager_portfolio import ManagerPortfolio


def _row_to_manager_portfolio(row: dict) -> ManagerPortfolio:
    return ManagerPortfolio(
        id=row["id"],
        portfolio_id=row["portfolio_id"],
        manager_id=row["manager_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class ManagerPortfolioRepository:
    @classmethod
    def get_by_manager_id(cls, db, manager_id: int) -> list[ManagerPortfolio]:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM manager_portfolios WHERE manager_id = %s",
            (manager_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [_row_to_manager_portfolio(row) for row in rows]

    @classmethod
    def create(cls, db, *, portfolio_id: int, manager_id: int) -> ManagerPortfolio:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO manager_portfolios (portfolio_id, manager_id) VALUES (%s, %s)",
            (portfolio_id, manager_id),
        )
        new_id = cursor.lastrowid
        cursor.close()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM manager_portfolios WHERE id = %s", (new_id,))
        row = cursor.fetchone()
        cursor.close()
        return _row_to_manager_portfolio(row)
