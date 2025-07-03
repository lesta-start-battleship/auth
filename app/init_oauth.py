from extensions import oauth
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

google = oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration", # noqa
    client_kwargs={"scope": "openid email profile"}
)