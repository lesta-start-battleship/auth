from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Enum as SQLEnum, ForeignKey, DateTime
from datetime import datetime
from enum import Enum


class Role(Enum):
    ADMINISTRATOR = "admin"
    MODERATOR = "moderator"
    USER = "user"


class CurrencyType(Enum):
    GUILD_RAGE = "guild_rage"
    GOLD = "gold"


class TransactionStatus(Enum):
    PENDING = "pending"
    RESERVED = "reserved"
    DECLINED = "declined"
    COMPLETED = "completed"
    FAILED = "failed"


class Base(DeclarativeBase):
    pass


class UserBase(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=True)
    surname: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(70), unique=True, nullable=False)
    h_password: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="role_enum"),
        default=Role.USER
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    currencies: Mapped["UserCurrency"] = relationship(
        "UserCurrency",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )
    transactions: Mapped[list["UserTransaction"]] = relationship(
        "UserTransaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"


class UserCurrency(Base):
    __tablename__ = "user_currencies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )
    guild_rage: Mapped[int] = mapped_column(default=0, nullable=False)
    gold: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    user: Mapped["UserBase"] = relationship(
        "UserBase", back_populates="currencies"
    )

    def __repr__(self):
        return (f"<UserCurrency of User {self.user_id}: "
                f"gold={self.gold}, guild_rage={self.guild_rage}>")


class UserTransaction(Base):
    __tablename__ = "user_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    currency_type: Mapped[CurrencyType] = mapped_column(
        SQLEnum(CurrencyType), nullable=False
    )
    amount: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus), default=TransactionStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    user: Mapped["UserBase"] = relationship(
        "UserBase", back_populates="transactions"
    )

    def __repr__(self):
        return (
            f"<UserTransaction {self.transaction_id}: "
            f"{self.amount} {self.currency_type} "
            f"for user {self.user_id} - {self.status}>"
        )
