import httpx
from sqlalchemy import select
from datetime import datetime, timedelta
from database.models import UserBase, Role, UserCurrency, DeviceLogin
from sqlalchemy.orm import Session
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from jose import jwt
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
            login_record.expires_at
        )

    return login_record


def request_device_login_details() -> httpx.Response:
    response = httpx.post(
        "https://oauth2.googleapis.com/device/code",
        data={"client_id": GOOGLE_CLIENT_ID, "scope": "openid email profile"}
    )
    return response


def poll_for_token(device_code) -> httpx.Response:
    response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        })
    return response


def get_or_create_user(session_db: Session, id_token: str) -> UserBase:
    user_info = jwt.get_unverified_claims(id_token)
    user = get_user_by_email(session_db, user_info["email"])

    if not user:
        user = create_user(
            session_db,
            email=user_info["email"],
            name=user_info.get("given_name"),
            surname=user_info.get("family_name"),
            username=user_info["email"].split("@")[0]
        )

    return user


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
