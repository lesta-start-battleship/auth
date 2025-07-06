from database.models import (
    UserBase, UserCurrency, UserTransaction, CurrencyType, TransactionStatus
)
from sqlalchemy.orm import Session


def user_exists(session_db: Session, user_id) -> bool:
    return session_db.query(UserBase).filter_by(id=user_id).first() is not None


def get_user_transaction(
    session_db, transaction_id: str, user_id: int
) -> UserTransaction | None:
    return session_db.query(UserTransaction).filter_by(
        transaction_id=transaction_id, user_id=user_id
    ).first()


def get_user_currency(
    session_db: Session, user_id: int
) -> UserCurrency | None:
    return session_db.query(UserCurrency).filter_by(user_id=user_id).first()


def process_compensation(
    session_db: Session,
    user_currency: UserCurrency,
    currency: CurrencyType,
    amount: int,
    transaction: UserTransaction
) -> None:
    setattr(
        user_currency,
        currency.value,
        getattr(user_currency, currency.value) + amount
    )
    transaction.status = TransactionStatus.FAILED
    session_db.commit()


def create_user_transaction_object(
    transaction_id: int,
    user_id: int,
    currency,
    amount: int,
    status: TransactionStatus
) -> UserTransaction:
    return UserTransaction(
        transaction_id=transaction_id, user_id=user_id,
        currency_type=currency, amount=amount, status=status
    )


def save_transaction(
    session_db: Session, transaction: UserTransaction
) -> None:
    session_db.add(transaction)
    session_db.commit()
