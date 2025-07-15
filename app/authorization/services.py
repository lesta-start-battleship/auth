from sqlalchemy.orm import Session
from database.models import UserBase, UserCurrency
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from kafka.producer import send_message_to_kafka
from flask import make_response, Response
from flask_jwt_extended import set_access_cookies, set_refresh_cookies


def get_user_by_username(
    session_db: Session,
    username: str
) -> UserBase | bool:
    """
    Получение пользователя по username
    """
    user = session_db.query(UserBase).filter_by(username=username).first()

    if user is None:
        return False

    return user


def create_user(
    session_db: Session,
    user_data: dict
) -> UserBase | Exception:
    """
    Создание пользователя
    """
    try:
        password = user_data.pop("password")
        user_data["h_password"] = generate_password_hash(password)
        user = UserBase(**user_data)
        session_db.add(user)
        session_db.flush()

        currency = UserCurrency(user_id=user.id)
        session_db.add(currency)
        session_db.commit()
        session_db.refresh(user)

        send_message_to_kafka(
            topic="prod.auth.fact.new-user.1",
            payload={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value.lower(),
                "gold": 0
            },
            target_service="scoreboard"
        )

        return user

    except SQLAlchemyError as e:
        session_db.rollback()
        raise e


def get_user_by_email(
    session_db: Session,
    email: str,
) -> UserBase | bool:
    """
    Получение пользователя по email
    """
    user = session_db.query(UserBase).filter(
        UserBase.email == email
    ).first()

    if user is None:
        return False

    return user


def create_response(
    user: UserBase,
    access_token: str,
    refresh_token: str,
    message: str,
    status_code: int
) -> Response:
    """
    Унифицированное создание ответа

    :param user: объект пользователя
    :param access_token: access токен
    :param refresh_token: refresh токен
    :param message: сообщение
    :param status_code: код статуса
    :return: экземпляр Response с данными пользователя в теле, токенами в заголовках и куках
    """
    response = make_response({
        "message": message,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "currencies": {
                "guild_rage": user.currencies.guild_rage,
                "gold": user.currencies.gold
            }
        }
    }, status_code)

    response.headers["Authorization"] = f"Bearer {access_token}"
    response.headers["Refresh-Token"] = f"Bearer {refresh_token}"

    set_access_cookies(
        response,
        access_token,
        max_age=60 * 60 * 24
    )
    set_refresh_cookies(
        response,
        refresh_token,
        max_age=60 * 60 * 24 * 7
    )

    return response
