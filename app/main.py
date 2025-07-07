from datetime import datetime, timezone, timedelta

from authorization.auth import auth_blueprint
from authorization.google import api_routes # noqa
from authorization.yandex import api_routes # noqa

from users.users import user_blueprint

from extensions import jwt_redis_blocklist, oauth

from errors import HttpError
# from signals import (
#     user_registered_handler, registration_user_signal,
#     change_username_handler, change_username_signal
# )

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
    FLASK_SECRET_KEY,
    JWT_SECRET_KEY,
    logger
)


app = Flask(__name__)

app.config["SECRET_KEY"] = FLASK_SECRET_KEY
app.config["SWAGGER"] = {"openapi": "3.0.0",}
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = JWT_ACCESS_TOKEN_EXPIRES
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = JWT_REFRESH_TOKEN_EXPIRES
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_CSRF_PROTECT"] = True

# registration_user_signal.connect(user_registered_handler)
# change_username_signal.connect(change_username_handler)

app.register_blueprint(auth_blueprint, url_prefix="/api/v1/auth")
app.register_blueprint(user_blueprint, url_prefix="/api/v1/users")

swagger = Swagger(app, template_file="api_doc.yaml")
jwt = JWTManager(app)
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
    # Thread(target=start_kafka_consumer, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
