from datetime import datetime
from authorization.auth import BaseAuthView
from authorization.auth import auth_blueprint
from authorization.oauth.google.services import (
    get_device_login_record, request_device_login_details, poll_for_token,
    get_or_create_user
)
from authorization.oauth.services import (
    get_user_by_email, create_user, create_device_login_record,
    delete_device_login_record
)
from init_oauth import google
from signals import registration_user_signal
from decorators import with_session
from flask import url_for, make_response, jsonify, request
from flask.views import MethodView
from flask_jwt_extended import set_access_cookies, set_refresh_cookies
from config import logger, GOOGLE_AUTH_URL


class GoogleLogin(MethodView):
    def get(self):
        logger.info("Запрос на авторизацию через Google из браузера")
        redirect_uri = url_for("Auth.google_authorize", _external=True)

        return google.authorize_redirect(redirect_uri)


class GoogleAuthorize(BaseAuthView):
    @with_session
    def get(self, session_db):
        try:
            token = google.authorize_access_token()
        except Exception as e:
            logger.error(f"Ошибка при получении токена от Google: {str(e)}")
            return jsonify(
                {"error": f"Не удалось получить токен Google: {str(e)}"}
            ), 400

        try:
            user_info = google.get(
                google.server_metadata["userinfo_endpoint"]
            ).json()
        except Exception as e:
            logger.error(f"Ошибка получения данных аккаунта Google: {str(e)}")
            return jsonify(
                {"error": f"Не удалось получить информацию о пользователе Google: {str(e)}"}
            ), 400

        email = user_info.get("email")
        user = get_user_by_email(session_db, email)

        if not user:
            logger.info(f"Создание нового пользователя с данными из Google")
            user = create_user(
                session_db,
                email=email,
                name=user_info.get("given_name"),
                surname=user_info.get("family_name"),
                username=email.split('@')[0]
            )
        else:
            logger.info(f"Пользователь Google найден: {user.username}")

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
            f"Аутентификация для {user.username} c помощью Google завершена, отправка ответа в браузер"
        )

        return jsonify(response_data), 200


class GoogleAuthLink(MethodView):
    def get(self):
        return jsonify({"google_url": GOOGLE_AUTH_URL})


class GoogleDeviceInit(BaseAuthView):
    @with_session
    def post(self, session_db):
        logger.info("Запрос на получение кода устройства и прочих данных от Google")
        response = request_device_login_details()

        if response.status_code != 200:
            logger.error("Детали для Google авторизации через устройство недоступны")
            return jsonify(
                {"error": "Device-based authentication is currently unavailable"}
            ), 500

        data = response.json()
        create_device_login_record(session_db, data, "GOOGLE")
        logger.info("Запись Google авторизации через устройство сохранена в БД")

        return jsonify({
            "user_code": data["user_code"],
            "device_code": data["device_code"],
            "verification_url": data["verification_url"],
            "expires_in": data["expires_in"],
            "interval": data["interval"]
        })


class GoogleDeviceCheck(BaseAuthView):
    @with_session
    def post(self, session_db):
        device_code = request.json.get("device_code")
        logger.info(f"Запрос токена по device_code: {device_code}")
        login_record = get_device_login_record(session_db, device_code)

        if not login_record:
            logger.error("device_code код неверный")
            return jsonify({"error": "Code is invalid"}), 400

        if login_record.expires_at < datetime.utcnow():
            logger.warning(
                "Локально: срок действия device_code истёк, но отправляем запрос в Google"
            )

        response = poll_for_token(device_code)
        response_data = response.json()
        error = response_data.get("error")

        if error == "authorization_pending":
            logger.info("Ожидание авторизации пользователя")
            return jsonify({"status": "pending"}), 428
        elif error == "expired_token":
            logger.warning("Код авторизации истёк")
            delete_device_login_record(session_db, login_record)
            return jsonify({"status": "expired"}), 400
        elif error == "access_denied":
            logger.warning("Пользователь отказался от авторизации")
            delete_device_login_record(session_db, login_record)
            return jsonify({"status": "denied"}), 400
        elif error:
            logger.error(f"Неизвестная ошибка: {error}")
            delete_device_login_record(session_db, login_record)
            return jsonify({"error": error}), 400

        id_token = response_data.get("id_token")
        if not id_token:
            logger.error("Нет id_token в ответе Google")
            return jsonify({"error": "No ID token provided"}), 400

        user = get_or_create_user(session_db, id_token)
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
        })


auth_blueprint.add_url_rule(
    "/login/google",
    view_func=GoogleLogin.as_view("google_login")
)
auth_blueprint.add_url_rule(
    "/google/callback",
    view_func=GoogleAuthorize.as_view("google_authorize")
)
auth_blueprint.add_url_rule(
    "/link/google",
    view_func=GoogleAuthLink.as_view("google_auth_link")
)
auth_blueprint.add_url_rule(
    "/google/device/init",
    view_func=GoogleDeviceInit.as_view("google_device_init")
)
auth_blueprint.add_url_rule(
    "/google/device/check",
    view_func=GoogleDeviceCheck.as_view("google_device_check")
)
