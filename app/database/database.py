from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

DSN = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"

engine = create_async_engine(DSN, echo=True)
session = async_sessionmaker(bind=engine, expire_on_commit=False)
