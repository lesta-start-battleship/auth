from extensions import oauth
from config import GOOGLE_CLIENT_ID_WEB, GOOGLE_CLIENT_SECRET_WEB

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID_WEB,
    client_secret=GOOGLE_CLIENT_SECRET_WEB,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration", # noqa
    client_kwargs={"scope": "openid email profile"}
)
