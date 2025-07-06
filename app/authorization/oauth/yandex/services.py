import requests
from sqlalchemy import select
from datetime import datetime, timedelta
from database.models import UserBase, Role, UserCurrency, DeviceLogin
from sqlalchemy.orm import Session
from config import YANDEX_CLIENT_ID
from extensions import device_login_redis
from authorization.device_cache import DeviceLoginCache
from database.models import OAuthProvider

cache = DeviceLoginCache(device_login_redis)


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


def get_user_by_id(session_db: Session, user_id: int) -> UserBase | None:
    return session_db.query(UserBase).filter_by(id=user_id).first()


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


def get_device_login_record(
    session_db: Session, device_code: str
) -> DeviceLogin | None:
    cached = cache.get(device_code)

    if cached:
        return cached

    login_record = session_db.query(DeviceLogin).filter_by(
        device_code=device_code
    ).first()

    if login_record:
        cache.set(
            login_record.device_code,
            login_record.provider,
            login_record.expires_at,
            is_verified=login_record.is_verified,
            user_id=login_record.user_id
        )

    return login_record


def get_params_for_oauth(device_code: str) -> dict[str, str]:
    return {
        "response_type": "code",
        "client_id": YANDEX_CLIENT_ID,
        "redirect_uri": "http://127.0.0.1:5001/api/v1/auth/yandex/device/verify",
        "force_confirm": "yes",
        "state": device_code
    }


def fetch_yandex_user_info(access_token: str) -> dict[str, str]:
    headers = {"Authorization": f"OAuth {access_token}"}
    response = requests.get("https://login.yandex.ru/info", headers=headers)

    return response.json()


def get_or_create_user(
    session_db: Session, user_info: dict[str, str | int]
) -> UserBase:
    email = user_info.get("default_email")
    user = get_user_by_email(session_db, email)

    if not user:
        user = create_user(
            session_db,
            email=email,
            name=user_info.get("first_name"),
            surname=user_info.get("last_name"),
            username=email.split("@")[0]
        )

    return user


def mark_device_login_verified(
    session_db: Session, login_record: DeviceLogin, user: UserBase
) -> None:
    login_record.user_id = user.id
    login_record.is_verified = True

    session_db.commit()

    cache.update(
        login_record.device_code,
        login_record.provider,
        login_record.expires_at,
        user.id
    )


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
