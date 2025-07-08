import requests
import uuid

from urllib.parse import urlencode
from datetime import datetime
from authorization.auth import BaseAuthView, auth_blueprint
from authorization.oauth.yandex.services import (
    get_user_by_id, get_device_login_record, get_params_for_oauth,
    fetch_yandex_user_info, get_or_create_user, mark_device_login_verified
)
from authorization.oauth.services import (
    get_user_by_email, create_user, create_device_login_record,
    delete_device_login_record
)
from decorators import with_session
from flask import url_for, make_response, jsonify, redirect, request
from flask.views import MethodView
from flask_jwt_extended import set_access_cookies, set_refresh_cookies
from config import (
    logger, YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET, YANDEX_AUTH_URL,
    YANDEX_REDIRECT_URL
)


class YandexLogin(MethodView):
    def get(self):
        logger.info("Запрос на авторизацию через Yandex из браузера")
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
            logger.error("Не получен код авторизации от Yandex")
            return jsonify(
                {"error": "Авторизация не удалась, код от Yandex не получен"}
            ), 400

        try:
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
        except Exception as e:
            logger.error(f"Ошибка при получении токена от Yandex: {str(e)}")
            return jsonify(
                {"error": f"Не удалось получить токен Yandex: {str(e)}"}
            ), 400

        try:
            headers = {"Authorization": f"OAuth {token_info['access_token']}"}
            user_info = requests.get(
                "https://login.yandex.ru/info", headers=headers
            ).json()
        except Exception as e:
            logger.error(
                f"Ошибка при получении информации о пользователе от Yandex: {str(e)}")
            return jsonify(
                {"error": f"Не удалось получить данные пользователя от Yandex: {str(e)}"}
            ), 400

        email = user_info.get("default_email")
        name = user_info.get("first_name")
        surname = user_info.get("last_name")
        user = get_user_by_email(session_db, email)

        if not user:
            logger.info(f"Создание нового пользователя с данными из Yandex")
            user = create_user(
                session_db, email=email, name=name,
                surname=surname, username=email.split("@")[0]
            )

        access_token = self._access_token(user)
        refresh_token = self._refresh_token(user)

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "currencies": {
                "guild_rage": user.currencies.guild_rage,
                "gold": user.currencies.gold
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
        logger.info(
            f"Аутентификация для {user.username} c помощью Yandex завершена, отправка ответа в браузер"
        )

        return jsonify(response_data), 200


class YandexAuthLink(MethodView):
    def get(self):
        return jsonify({"yandex_url": YANDEX_AUTH_URL})


class YandexDeviceInit(BaseAuthView):
    @with_session
    def post(self, session_db):
        logger.info("Запрос на получение кода устройства и прочих данных от Yandex")

        device_code = uuid.uuid4().hex
        expires_in = 600
        interval = 5
        params = get_params_for_oauth(device_code)
        verification_url = f"https://oauth.yandex.ru/authorize?{urlencode(params)}"
        data = {
            "device_code": device_code,
            "user_code": uuid.uuid4().hex[:6].upper(),
            "expires_in": expires_in
        }
        create_device_login_record(session_db, data, "YANDEX")
        logger.info("Запись Yandex авторизации через устройство сохранена в БД")

        return jsonify({
            "device_code": device_code,
            "verification_url": verification_url,
            "expires_in": expires_in,
            "interval": interval
        })


class YandexVerify(BaseAuthView):
    @with_session
    def get(self, session_db):
        code = request.args.get("code")
        device_code = request.args.get("state")

        if not code or not device_code:
            logger.error("Отсутствует параметр 'code' или 'state'")
            return jsonify({"error": "Missing code or device_code"}), 400

        logger.info(f"Получен callback с code={code} и state={device_code}")
        login_record = get_device_login_record(session_db, device_code)

        if not login_record:
            logger.error(f"Нет активной сессии для device_code={device_code}")
            return jsonify({"error": "No pending login session found"}), 404

        if login_record.expires_at < datetime.utcnow():
            logger.warning(
                f"Попытка верификации с истёкшим device_code={device_code}"
            )
            delete_device_login_record(session_db, login_record)
            return jsonify({"error": "Device login expired"}), 400

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": YANDEX_CLIENT_ID,
            "client_secret": YANDEX_CLIENT_SECRET,
            "redirect_uri": YANDEX_REDIRECT_URL
        }
        response = requests.post(
            "https://oauth.yandex.ru/token", data=token_data
        )

        if response.status_code != 200:
            logger.error(f"Ошибка при получении токена - {response.text}")
            return jsonify({"error": "Failed to fetch token"}), 400

        access_token = response.json().get("access_token")
        user_info = fetch_yandex_user_info(access_token)
        user = get_or_create_user(session_db, user_info)
        mark_device_login_verified(session_db, login_record, user)
        logger.info(f"Верификация прошла успешно")

        return f"<h1>Вы успешно вошли в аккаунт, можете вернуться обратно</h1>"


class YandexDeviceCheck(BaseAuthView):
    @with_session
    def post(self, session_db):
        device_code = request.json.get("device_code")
        logger.info(f"Запрос токена по device_code: {device_code}")

        if not device_code:
            logger.error("Отсутствует параметр 'device_code'")
            return jsonify({"error": "Missing device_code"}), 400

        login_record = get_device_login_record(session_db, device_code)
        if not login_record:
            logger.error("device_code код неверный")
            return jsonify({"error": "Code is invalid"}), 400

        if login_record.expires_at < datetime.utcnow():
            logger.warning("Код авторизации истёк")
            delete_device_login_record(session_db, login_record)
            return jsonify({"status": "expired"}), 400

        if not login_record.is_verified:
            logger.info("Ожидание авторизации пользователя")
            return jsonify({"status": "pending"}), 428

        user = get_user_by_id(session_db, login_record.user_id)
        logger.info("Авторизация через устройство успешно подтверждена")
        delete_device_login_record(session_db, login_record)

        return jsonify({
            "access_token": self._access_token(user),
            "refresh_token": self._refresh_token(user),
            "status": "authenticated",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "currencies": {
                    "guild_rage": user.currencies.guild_rage,
                    "gold": user.currencies.gold
                }
            }
        }), 200


auth_blueprint.add_url_rule(
    "/login/yandex",
    view_func=YandexLogin.as_view("yandex_login")
)
auth_blueprint.add_url_rule(
    "/yandex/callback",
    view_func=YandexAuthorize.as_view("yandex_authorize")
)
auth_blueprint.add_url_rule(
    "/link/yandex",
    view_func=YandexAuthLink.as_view("yandex_auth_link")
)
auth_blueprint.add_url_rule(
    "/yandex/device/init",
    view_func=YandexDeviceInit.as_view("yandex_device_init")
)
auth_blueprint.add_url_rule(
    "/yandex/device/verify",
    view_func=YandexVerify.as_view("yandex_verify")
)
auth_blueprint.add_url_rule(
    "/yandex/device/check",
    view_func=YandexDeviceCheck.as_view("yandex_device_check")
)
