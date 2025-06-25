from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer
from datetime import datetime


class Base(DeclarativeBase):
    __abstract__ = True  #

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class UserBase(Base):
    __tablename__ = "users"
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    surname: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    h_password: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    silver: Mapped[int] = mapped_column(default=0)
    gold: Mapped[int] = mapped_column(default=0)
    role: Mapped[str] = mapped_column(
        default="user"
    )  # Сделать вторую таблицу с ролями, а сюда присваивать айди с нужной ролью (?)
    datetime: Mapped[str] = mapped_column(default=datetime.now)
