from server.db.base import Base
from server.db.session import engine


def init_orm() -> None:
    from server.models import orm_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
