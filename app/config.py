import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import timedelta

from extensions import oauth

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("app.log", maxBytes=20000, backupCount=2)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console_handler)

load_dotenv(override=True)

FLASK_PORT = os.getenv("FLASK_PORT")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

VERSION = os.getenv("VERSION")

JWT_ACCESS_BLOCKLIST = os.getenv("JWT_ACCESS_BLOCKLIST", timedelta(hours=1))
JWT_ACCESS_TOKEN_EXPIRES = os.getenv(
    "JWT_ACCESS_TOKEN_EXPIRES",
    timedelta(days=1)
)
JWT_REFRESH_TOKEN_EXPIRES = os.getenv(
    "JWT_REFRESH_TOKEN_EXPIRES",
    timedelta(days=7)
)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = f"http://127.0.0.1:{FLASK_PORT}/api/v1/auth/login/google"

YANDEX_CLIENT_ID = os.getenv('YANDEX_CLIENT_ID')
YANDEX_CLIENT_SECRET = os.getenv('YANDEX_CLIENT_SECRET')
YANDEX_AUTH_URL = f"http://127.0.0.1:{FLASK_PORT}/api/v1/auth/login/yandex"

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration", # noqa
    client_kwargs={"scope": "openid email profile"}
)
