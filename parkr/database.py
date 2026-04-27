from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from parkr.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    with engine.begin() as conn:
        # TEMP: skip PostGIS for deployment
        # conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        Base.metadata.create_all(bind=conn)