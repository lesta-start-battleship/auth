from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DSN = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"localhost:5432/{POSTGRES_DB}"
)

engine = create_engine(DSN)
session = sessionmaker(bind=engine, expire_on_commit=False)
