from typing import Type

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Session, sessionmaker


class Base(DeclarativeBase, MappedAsDataclass):
    pass


def get_db(database_url: str) -> tuple[sessionmaker[Session], Type[Base], Engine]:
    engine = create_engine(database_url)
    return sessionmaker(bind=engine), Base, engine
