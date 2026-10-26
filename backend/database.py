from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import config

# FastAPI handles requests on different threads, so SQLite must allow that
engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


# SQLite ignores foreign keys unless this is switched on for each connection
@event.listens_for(engine, "connect")
def turn_on_foreign_keys(connection, _record):
    connection.execute("PRAGMA foreign_keys=ON")


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
