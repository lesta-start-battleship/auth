import requests
from database.models import UserBase, Role, UserCurrency, DeviceLogin
from sqlalchemy.orm import Session
from config import YANDEX_CLIENT_ID, YANDEX_REDIRECT_URL
from extensions import device_login_redis
from authorization.oauth.device_cache import DeviceLoginCache
from authorization.oauth.services import get_user_by_email, create_user

cache = DeviceLoginCache(device_login_redis)


def get_user_by_id(session_db: Session, user_id: int) -> UserBase | None:
    return session_db.query(UserBase).filter_by(id=user_id).first()


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
            login_record.device_code, login_record.provider,
            login_record.expires_at, is_verified=login_record.is_verified,
            user_id=login_record.user_id
        )

    return login_record


def get_params_for_oauth(device_code: str) -> dict[str, str]:
    return {
        "response_type": "code",
        "client_id": YANDEX_CLIENT_ID,
        "redirect_uri": YANDEX_REDIRECT_URL,
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
        login_record.device_code, login_record.provider,
        login_record.expires_at, user.id
    )
