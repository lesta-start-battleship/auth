from sqlalchemy.orm import Session, joinedload
from database.models import UserBase
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from werkzeug.security import generate_password_hash
from kafka.producer import send_message_to_kafka


def get_user_by_id(
    session_db: Session,
    user_id: int
) -> UserBase | bool:
    """
    Получение пользователя по id

    :param session_db: сессия базы данных
    :param user_id: id пользователя
    :return: UserBase | bool
    """
    try:
        user = session_db.get(UserBase, user_id)

        if user is None:
            return False

        return user

    except SQLAlchemyError as e:
        raise e


def get_full_user_by_id(session_db: Session, user_id: int) -> UserBase | bool:
    """
    Получение полной информации о пользователе по id

    :param session_db: сессия базы данных
    :param user_id: id пользователя
    :return: UserBase | bool
    """
    try:
        user = (
            session_db.query(UserBase)
            .options(joinedload(UserBase.currencies))
            .filter(UserBase.id == user_id)
            .one_or_none()
        )

        return user if user else False

    except SQLAlchemyError as e:
        raise e


def get_users(
    session_db: Session,
    user_ids: List[int]
) -> Optional[List[UserBase]]:
    """
    Получение списка пользователей по id

    :param session_db: сессия базы данных
    :param user_ids: список id пользователей
    :return: Optional[List[UserBase]]
    """
    try:
        users = (
            session_db.query(UserBase)
            .options(joinedload(UserBase.currencies))
            .filter(UserBase.id.in_(user_ids))
            .all()
        )

        if not users:
            return None

        return users

    except SQLAlchemyError as e:
        raise e


def update_user(
    session_db: Session,
    user_id: int,
    **kwargs
) -> UserBase | bool:
    """
    Обновление пользователя по id

    :param session_db: сессия базы данных
    :param user_id: id пользователя
    :param kwargs: параметры для обновления
    :return: UserBase | bool
    """
    try:
        user = get_user_by_id(session_db, user_id)
        if not user:
            return False

        original_username = user.username
        if "password" in kwargs:
            kwargs["h_password"] = generate_password_hash(kwargs["password"])

        for key, value in kwargs.items():
            setattr(user, key, value)

        session_db.commit()
        session_db.refresh(user)

        if "username" in kwargs and kwargs["username"] != original_username:
            send_message_to_kafka(
                topic="prod.auth.fact.username-change.1",
                payload={"user_id": user.id, "username": user.username},
                target_service="scoreboard"
            )

        return user

    except SQLAlchemyError as e:
        session_db.rollback()
        raise e


def delete_user(session_db: Session, user_id: int) -> bool:
    """
    Удаление пользователя

    :param session_db: сессия базы данных
    :param user_id: id пользователя
    :return: bool
    """
    try:
        user = get_user_by_id(session_db, user_id)
        if not user:
            return False

        session_db.delete(user)
        session_db.commit()

        return True

    except SQLAlchemyError as e:
        session_db.rollback()
        raise e
