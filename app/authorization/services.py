from sqlalchemy.orm import Session
from database.models import UserBase, UserCurrency
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from kafka.producer import send_message_to_kafka


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
