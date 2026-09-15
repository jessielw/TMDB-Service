from typing import Type

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Session, sessionmaker

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
}


class Base(DeclarativeBase, MappedAsDataclass):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def get_db(database_url: str) -> tuple[sessionmaker[Session], Type[Base], Engine]:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine), Base, engine
