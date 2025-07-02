from sqlalchemy import select

from database.models import UserBase, Role, UserCurrency
from sqlalchemy.orm import Session


def get_user_by_email(
    session_db: Session,
    email: str
) -> UserBase | None:
    result = session_db.execute(select(UserBase).filter_by(email=email))
    return result.scalar_one_or_none()


def create_user(
    session_db: Session,
    email: str,
    name: str,
    surname: str,
    username: str
) -> UserBase:
    new_user = UserBase(
        username=username,
        name=name,
        surname=surname,
        email=email,
        is_active=True,
        role=Role.USER
    )
    session_db.add(new_user)
    session_db.flush()
    currency = UserCurrency(user_id=new_user.id)

    session_db.add(currency)
    session_db.commit()

    session_db.refresh(new_user)

    return new_user
