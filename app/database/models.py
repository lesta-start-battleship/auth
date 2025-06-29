from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Enum as SQLEnum, ForeignKey
from datetime import datetime
from enum import Enum


class Role(Enum):
    ADMINISTRATOR = "admin"
    MODERATOR = "moderator"
    USER = "user"


class Base(DeclarativeBase):
    __abstract__ = True 

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class UserBase(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    surname: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    h_password: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, name="role_enum"))  
    created_at: Mapped[str] = mapped_column(default=datetime.now)

class Balance(Base):
    __tablename__ = "balance"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    silver: Mapped[int] = mapped_column(default=0)
    gold: Mapped[int] = mapped_column(default=0)