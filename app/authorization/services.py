from flask import request
from database.models import UserBase
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash


async def get_user_by_username(username: str) -> UserBase | bool:
    """
    Получение пользователя по username
    """
    user = request.db_session.query(UserBase).filter_by(username=username).first()

    if user is None:
        return False

    return user

async def create_user(user_data: dict) -> UserBase | Exception:
    """
    Создание пользователя
    """
    try:
        user_data["password"] = generate_password_hash(user_data["password"])
        user = UserBase(**user_data)
        request.db_session.add(user)
        request.db_session.commit()

        return user

    except SQLAlchemyError as e:
        request.db_session.rollback()
        raise e
