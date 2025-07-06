import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import timedelta


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("app.log", maxBytes=20000, backupCount=2)
logger.addHandler(handler)

load_dotenv(override=True)

FLASK_PORT = os.getenv("FLASK_PORT")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

CACHE_REDIS_HOST = os.getenv("CACHE_REDIS_HOST")
CACHE_REDIS_PORT = os.getenv("CACHE_REDIS_PORT")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
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

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_CLIENT_ID_WEB = os.getenv("GOOGLE_CLIENT_ID_WEB")
GOOGLE_CLIENT_SECRET_WEB = os.getenv("GOOGLE_CLIENT_SECRET_WEB")
GOOGLE_AUTH_URL = f"{SERVER_ADDRESS}:{FLASK_PORT}/api/v1/auth/login/google"

YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")
YANDEX_CLIENT_SECRET = os.getenv("YANDEX_CLIENT_SECRET")
YANDEX_AUTH_URL = f"{SERVER_ADDRESS}:{FLASK_PORT}/api/v1/auth/login/yandex"
YANDEX_REDIRECT_URL = f"{SERVER_ADDRESS}:{FLASK_PORT}/api/v1/auth/yandex/device/verify"

KAFKA_ADDRESS = os.getenv("KAFKA_ADDRESS")
