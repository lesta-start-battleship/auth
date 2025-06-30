import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import timedelta

from extensions import oauth

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("app.log", maxBytes=20000, backupCount=2)
logger.addHandler(handler)

load_dotenv(override=True)

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

VERSION = os.getenv("VERSION")

JWT_ACCESS_BLOCKLIST = os.getenv("JWT_ACCESS_BLOCKLIST", timedelta(hours=1))
JWT_ACCESS_TOKEN_EXPIRES = os.getenv("JWT_ACCESS_TOKEN_EXPIRES", timedelta(days=1))
JWT_REFRESH_TOKEN_EXPIRES = os.getenv("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=7))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)
