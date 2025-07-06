import httpx
from database.models import (
    UserBase, Role, UserCurrency, DeviceLogin, OAuthProvider
)
from sqlalchemy.orm import Session
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from jose import jwt
from extensions import device_login_redis
from authorization.oauth.device_cache import DeviceLoginCache
from authorization.oauth.services import get_user_by_email, create_user

cache = DeviceLoginCache(device_login_redis)


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
