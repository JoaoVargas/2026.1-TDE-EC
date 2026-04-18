from sqlalchemy import select

from config.db import Base, SessionLocal
from models import orm_models  # noqa: F401


def fetch_all_from_table(table_name):
    if table_name not in Base.metadata.tables:
        return []

    table = Base.metadata.tables[table_name]
    with SessionLocal() as db:
        rows = db.execute(select(table)).mappings().all()
        if not rows:
            return []

        # Template-friendly output shape that preserves old tuple-like semantics.
        columns = list(rows[0].keys())
        records = [tuple(row[col] for col in columns) for row in rows]
        return records
