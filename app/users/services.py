from flask import request
from database.models import UserBase
from sqlalchemy.exc import SQLAlchemyError
from config import logger
from typing import List, Optional


async def get_user_by_id(user_id: int) -> UserBase | bool:
    """
    Получение пользователя по id

    :param user_id: id пользователя
    :return: UserBase | bool
    """
    try:
        user = request.db_session.get(UserBase, user_id)

        if user is None:
            return False

        return user

    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        raise e


async def get_users(user_ids: List[int]) -> Optional[List[UserBase]]:
    """
    Получение списка пользователей по id

    :param user_ids: список id пользователей
    :return: Optional[List[UserBase]]
    """
    try:
        users = request.db_session.query(UserBase).filter(UserBase.id.in_(user_ids)).all()

        if not users:
            return None

        return users

    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        raise e


async def update_user(user_id: int, **kwargs) -> UserBase | bool:
    """
    Обновление пользователя по id

    :param user_id: id пользователя
    :param kwargs: параметры для обновления
    :return: UserBase | bool
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return False

        for key, value in kwargs.items():
            setattr(user, key, value)

        request.db_session.commit()

        return user

    except SQLAlchemyError as e:
        request.db_session.rollback()
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise e

async def delete_user(user_id: int) -> bool:
    """
    Удаление пользователя

    :param user_id: id пользователя
    :return: bool
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return False

        request.db_session.delete(user)
        request.db_session.commit()

    except SQLAlchemyError as e:
        request.db_session.rollback()
        logger.error(f"Ошибка при удалении пользователя: {e}")
        raise e

