from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from decouple import config
from urllib.parse import quote_plus

DB_URL = (
    f"postgresql+psycopg2://{config('DB_USER')}:{quote_plus(config('DB_PASSWORD'))}"
    f"@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}"
)

engine = create_engine(DB_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Creates chat_messages table in your existing Django DB."""
    Base.metadata.create_all(bind=engine)