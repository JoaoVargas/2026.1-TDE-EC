from sqlalchemy import select

from server.db.base import Base
from server.db.session import SessionLocal
from server.models import orm_models  # noqa: F401


def fetch_all_from_table(table_name: str) -> list[tuple[object, ...]]:
    if table_name not in Base.metadata.tables:
        return []

    table = Base.metadata.tables[table_name]
    with SessionLocal() as db:
        rows = db.execute(select(table)).mappings().all()
        if not rows:
            return []

        columns = list(rows[0].keys())
        return [tuple(row[col] for col in columns) for row in rows]
