from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Enum as SQLEnum, ForeignKey, DateTime
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
    name: Mapped[str] = mapped_column(String(20), nullable=True)
    surname: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    h_password: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, name="role_enum"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    currencies: Mapped["UserCurrency"] = relationship(
        "UserCurrency", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"


class UserCurrency(Base):
    __tablename__ = "user_currencies"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    silver: Mapped[int] = mapped_column(default=0)
    gold: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["UserBase"] = relationship(
        "UserBase", back_populates="currencies"
    )

    def __repr__(self):
        return (f"<UserCurrency of User {self.user_id}: "
                f"gold={self.gold}, silver={self.silver}>")
