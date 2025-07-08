import os

from datetime import datetime, timezone, timedelta
from threading import Thread
from kafka.consumer import start_consumer_loop

from authorization.auth import auth_blueprint
from authorization.oauth.google import api_routes # noqa
from authorization.oauth.yandex import api_routes # noqa

from users.users import user_blueprint
from currencies.routs import currencies_blueprint
from admin import (
    admin,
    UserBaseAdminView,
    UserCurrencyAdminView,
    UserTransactionAdminView
)
from database.database import session
from database.models import UserBase, UserCurrency, UserTransaction

from extensions import jwt_redis_blocklist, oauth, mail

from errors import HttpError
from signals import (
    user_registered_handler, registration_user_signal,
)
from flask import Flask, Response, jsonify
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    create_access_token,
    set_access_cookies
)

from config import (
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES,
    logger,
    FLASK_PORT,
    VERSION
)


app = Flask(__name__)

with open("jwt_private_key", "r") as f:
    app.config["JWT_PRIVATE_KEY"] = f.read()

with open("jwt_pub_key.pub", "r") as f:
    app.config["JWT_PUBLIC_KEY"] = f.read()

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
app.config["SWAGGER"] = {"openapi": "3.0.0", "version": VERSION}
app.config["FLASK_ADMIN_SWATCH"] = "slate"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = JWT_ACCESS_TOKEN_EXPIRES
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = JWT_REFRESH_TOKEN_EXPIRES
app.config["JWT_ALGORITHM"] = "RS256"
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_CSRF_PROTECT"] = True

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

registration_user_signal.connect(user_registered_handler)

app.register_blueprint(auth_blueprint, url_prefix="/api/v1/auth")
app.register_blueprint(user_blueprint, url_prefix="/api/v1/users")
app.register_blueprint(currencies_blueprint, url_prefix="/api/v1/currencies")

admin.add_view(UserBaseAdminView(UserBase, session()))
admin.add_view(UserCurrencyAdminView(UserCurrency, session()))
admin.add_view(UserTransactionAdminView(UserTransaction, session()))

admin.init_app(app)

swagger = Swagger(app, template_file="api_doc.yaml")
jwt = JWTManager(app)
mail.init_app(app)
oauth.init_app(app)


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header: dict, jwt_payload: dict):
    """
    Проверка, находится ли токен в блок-листе
    """
    jti = jwt_payload["jti"]

    return jwt_redis_blocklist.get(jti) is not None


@app.errorhandler(HttpError)
def error_handler(err: HttpError):
    """
    Обработчик ошибок
    """
    http_response = jsonify({"error": err.message})
    http_response.status_code = err.status_code
    logger.error(f"Ошибка {err.status_code}: {err.message}")
    return http_response


@app.after_request
def refresh_expiring_jwts(response: Response):
    """
    Функция для неявноего обновления jwt токенов
    """
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            claims = get_jwt()
            access_token = create_access_token(
                identity=get_jwt_identity(),
                additional_claims={
                    "username": claims["username"],
                    "role": claims["role"]
                }
            )
            set_access_cookies(
                response,
                access_token,
                max_age=60*60*24
            )

            return response

    except (RuntimeError, KeyError):
        return response

    finally:
        return response


if __name__ == "__main__":
    Thread(target=start_consumer_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=FLASK_PORT)
