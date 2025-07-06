from config import (
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DSN = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(DSN)
session = sessionmaker(bind=engine, expire_on_commit=False)
