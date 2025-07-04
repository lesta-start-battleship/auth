from database.models import UserCurrency
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from users.services import get_user_by_id


def get_user_currencies(
    user_id: int,
    session_db: Session
) -> UserCurrency | bool:
    """
    Получение валют пользователя

    :param user_id: id пользователя
    :param session_db: сессия базы данных
    :return: UserCurrency | bool
    """
    try:
        user = get_user_by_id(session_db, user_id)
        if not user:
            return False

        return (
            session_db.query(UserCurrency)
            .filter(UserCurrency.user_id == user_id)
            .first()
        )
    except SQLAlchemyError as e:
        raise e


def update_user_currencies(
    user_id: int,
    session_db: Session,
    **kwargs
) -> UserCurrency | bool:
    """
    Обновление валют пользователя

    :param user_id: id пользователя
    :param session_db: сессия базы данных
    :param kwargs: параметры для обновления
    :return: UserCurrency | bool
    """
    try:
        user = get_user_by_id(session_db, user_id)
        if not user:
            return False

        user_currencies = (
            session_db.query(UserCurrency)
            .filter(UserCurrency.user_id == user_id)
            .first()
        )
        if not user_currencies:
            return False

        for key, value in kwargs.items():
            setattr(user_currencies, key, value)

        session_db.add(user_currencies)
        session_db.commit()

        return user_currencies

    except SQLAlchemyError as e:
        raise e
