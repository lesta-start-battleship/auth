from flask import url_for
from flask_restx import Resource

from app.authorization.google.services import get_user_by_email, create_user
from authorization.namespace import auth_ns
from app.config import google
from app.decorators import with_session


@auth_ns.route('/login/google')
class GoogleLogin(Resource):
    @auth_ns.doc(
        responses={
            201: "User registered successfully"
        },
        description="Registration a new user",
    )
    def get(self):
        redirect_uri = url_for("auth_google_authorize", _external=True)
        return google.authorize_redirect(redirect_uri)


@auth_ns.route('/google/callback', endpoint="auth_google_authorize")
class GoogleAuthorize(Resource):
    @with_session
    def get(self, session_db):
        token = google.authorize_access_token()
        user_info = google.get(
            google.server_metadata["userinfo_endpoint"]
        ).json()
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

        user = get_user_by_email(session_db, email)

        if not user:
            user = create_user(session_db, email=email, username=email.split('@')[0])

        return {
            "message": "Login was successful!",
            "user": {
                "email": email,
                "name": name,
                "picture": picture
            }
        }
