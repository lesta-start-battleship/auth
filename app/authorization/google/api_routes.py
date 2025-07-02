from urllib.parse import urlencode, parse_qs

from authorization.auth import BaseAuthView
from authorization.auth import auth_blueprint
from authorization.google.services import get_user_by_email, create_user
from config import google
from signals import registration_user_signal
from decorators import with_session
from flask import url_for, make_response, jsonify, request, redirect
from flask.views import MethodView
from flask_jwt_extended import set_access_cookies, set_refresh_cookies


class GoogleLogin(MethodView):
    def get(self):
        cli_redirect_uri = request.args.get("redirect_uri")
        redirect_uri = url_for("Auth.google_authorize", _external=True)

        return google.authorize_redirect(
            redirect_uri, state=urlencode({"cli_redirect": cli_redirect_uri})
        )


class GoogleAuthorize(BaseAuthView):
    @with_session
    def get(self, session_db):
        token = google.authorize_access_token()  # noqa
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

            registration_user_signal.send(
                self.__class__,
                user_id=user.id
            )

        access_token = self._access_token(user)
        refresh_token = self._refresh_token(user)

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "currencies": {
                "guild_rage": user.currencies.guild_rage if user.currencies else 0,
                "gold": user.currencies.gold if user.currencies else 0
            }
        }

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_data
        }

        response = make_response(response_data, 200)

        set_access_cookies(
            response,
            access_token,
            max_age=60 * 60 * 24
        )
        set_refresh_cookies(
            response,
            refresh_token,
            max_age=60 * 60 * 24 * 7
        )

        state = request.args.get("state")
        parsed = parse_qs(state)
        cli_redirect = parsed.get("cli_redirect", [None])[0]

        if cli_redirect:
            from json import dumps
            import base64

            encoded = base64.urlsafe_b64encode(
                dumps(response_data).encode()
            ).decode()

            return redirect(f"{cli_redirect}?data={encoded}")
        return jsonify(response_data), 200


auth_blueprint.add_url_rule(
    "/login/google",
    view_func=GoogleLogin.as_view("google_login")
)
auth_blueprint.add_url_rule(
    "/google/callback",
    view_func=GoogleAuthorize.as_view("google_authorize")
)
