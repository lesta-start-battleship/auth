from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from database.models import UserBase, Role, UserCurrency, DeviceLogin, OAuthProvider
from extensions import device_login_redis
from authorization.oauth.device_cache import DeviceLoginCache

from kafka.kafka import send_scoreboard_event

cache = DeviceLoginCache(device_login_redis)


def get_user_by_email(
    session_db: Session,
    email: str
) -> UserBase | None:
    result = session_db.execute(select(UserBase).filter_by(email=email))
    return result.scalar_one_or_none()


def create_user(
    session_db: Session, email: str, name: str, surname: str, username: str
) -> UserBase:
    new_user = UserBase(
        username=username, name=name, surname=surname,
        email=email, is_active=True, role=Role.USER
    )
    session_db.add(new_user)
    session_db.flush()

    currency = UserCurrency(user_id=new_user.id)

    session_db.add(currency)
    session_db.commit()
    session_db.refresh(new_user)

    send_scoreboard_event(
        "prod.auth.fact.new-user.1",
        {
            "user_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "gold": 0
        })

    return new_user


def create_device_login_record(
    session_db: Session, data: dict[str, str | int], provider: str
) -> DeviceLogin:

    if isinstance(provider, str):
        provider = OAuthProvider(provider.lower())

    expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
    login_record = DeviceLogin(
        device_code=data["device_code"],
        user_code=data["user_code"],
        provider=provider,
        expires_at=expires_at
    )
    session_db.add(login_record)
    session_db.commit()

    cache.set(login_record.device_code, provider, expires_at)
    return login_record


def delete_device_login_record(
    session_db: Session, login_record: DeviceLogin
) -> None:
    cache.delete(login_record.device_code)

    record = session_db.query(DeviceLogin).filter_by(
        device_code=login_record.device_code
    ).first()

    if record:
        session_db.delete(record)
        session_db.commit()
