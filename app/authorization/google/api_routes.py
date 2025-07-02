from flask import url_for, make_response, jsonify
from flask.views import MethodView

from authorization.google.services import get_user_by_email, create_user
from authorization.auth import auth_blueprint
from config import google
from decorators import with_session
from authorization.auth import BaseAuthView
from flask_jwt_extended import set_access_cookies, set_refresh_cookies


class GoogleLogin(MethodView):

    def get(self):
        redirect_uri = url_for("Auth.google_authorize", _external=True)
        return google.authorize_redirect(redirect_uri)


class GoogleAuthorize(BaseAuthView):
    @with_session
    def get(self, session_db):
        token = google.authorize_access_token() # noqa
        user_info = google.get(
            google.server_metadata["userinfo_endpoint"]
        ).json()
        email = user_info.get("email")

        user = get_user_by_email(session_db, email)

        if not user:
            user = create_user(
                session_db,
                email=email,
                name=user_info.get("given_name"),
                surname=user_info.get("family_name"),
                username=email.split('@')[0]
            )

        access_token = self._access_token(user)
        refresh_token = self._refresh_token(user)

        response = make_response({
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200)

        set_access_cookies(
            response,
            access_token,
            max_age=60*60*24
        )
        set_refresh_cookies(
            response,
            refresh_token,
            max_age=60*60*24*7
        )

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token
        })


auth_blueprint.add_url_rule(
    "/login/google",
    view_func=GoogleLogin.as_view("google_login")
)
auth_blueprint.add_url_rule(
    "/google/callback",
    view_func=GoogleAuthorize.as_view("google_authorize")
)
