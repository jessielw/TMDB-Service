from tmdb_service.globals import Base, db


def create_tables():
    # get the engine from sessionmaker (db)
    engine = db.kw["bind"]
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
