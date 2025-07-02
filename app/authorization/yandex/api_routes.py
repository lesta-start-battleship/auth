from urllib.parse import urlencode, parse_qs

import requests
from authorization.auth import BaseAuthView
from authorization.auth import auth_blueprint
from authorization.google.services import get_user_by_email, create_user
from config import YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET
from decorators import with_session
from flask import url_for, make_response, jsonify, redirect, request
from flask.views import MethodView
from flask_jwt_extended import set_access_cookies, set_refresh_cookies


class YandexLogin(MethodView):
    def get(self):
        cli_redirect_uri = request.args.get("redirect_uri")
        redirect_uri = url_for("Auth.yandex_authorize", _external=True)
        state = urlencode(
            {"cli_redirect": cli_redirect_uri}
        ) if cli_redirect_uri else None

        params = {
            "response_type": "code",
            "client_id": YANDEX_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "display": "popup",
            "force_confirm": "yes"
        }

        if state:
            params["state"] = state

        auth_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"

        return redirect(auth_url)


class YandexAuthorize(BaseAuthView):
    @with_session
    def get(self, session_db):
        code = request.args.get('code')

        if not code:
            return {"message": "Authorization failed, no code provided"}

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": YANDEX_CLIENT_ID,
            "client_secret": YANDEX_CLIENT_SECRET
        }

        response = requests.post(
            "https://oauth.yandex.ru/token", data=token_data
        )
        response.raise_for_status()
        token_info = response.json()

        headers = {"Authorization": f"OAuth {token_info['access_token']}"}
        user_info = requests.get(
            "https://login.yandex.ru/info", headers=headers
        ).json()
        email = user_info.get("default_email")
        name = user_info.get("first_name")
        surname = user_info.get("last_name")

        user = get_user_by_email(session_db, email)

        if not user:
            user = create_user(
                session_db,
                email=email,
                name=name,
                surname=surname,
                username=email.split("@")[0]
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
    "/login/yandex",
    view_func=YandexLogin.as_view("yandex_login")
)
auth_blueprint.add_url_rule(
    "/yandex/callback",
    view_func=YandexAuthorize.as_view("yandex_authorize")
)
