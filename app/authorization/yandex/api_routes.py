from flask import url_for, make_response, jsonify, redirect, request
from flask.views import MethodView

from authorization.google.services import get_user_by_email, create_user
from authorization.auth import auth_blueprint
from decorators import with_session
from config import YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET
from authorization.auth import BaseAuthView
from flask_jwt_extended import set_access_cookies, set_refresh_cookies
from urllib.parse import urlencode
import requests


class YandexLogin(MethodView):
    def get(self):
        redirect_uri = url_for("Auth.yandex_authorize", _external=True)
        params = {
            "response_type": "code",
            "client_id": YANDEX_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "display": "popup",
            "force_confirm": "yes"
        }
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
    "/login/yandex",
    view_func=YandexLogin.as_view("yandex_login")
)
auth_blueprint.add_url_rule(
    "/yandex/callback",
    view_func=YandexAuthorize.as_view("yandex_authorize")
)
