from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    String, Integer, Enum as SQLEnum, ForeignKey, DateTime, Boolean
)
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


class OAuthProvider(Enum):
    GOOGLE = "google"
    YANDEX = "yandex"


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )


class UserBase(Base):
    __tablename__ = "users"

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
        uselist=False,
        lazy="joined"
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

    transaction_id: Mapped[str] = mapped_column(
        String(64),
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


class DeviceLogin(Base):
    __tablename__ = "device_logins"

    device_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    user_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    provider: Mapped[OAuthProvider] = mapped_column(
        SQLEnum(OAuthProvider), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<DeviceLogin {self.device_code}, user_code={self.user_code}, "
            f"user_id={self.user_id}, verified={self.is_verified}>"
        )
