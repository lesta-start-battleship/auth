import redis
from authorization.namespace import auth_ns
from users.namespace import user_ns
from flask import Flask
from flask_restx import Api
from config import JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES, logger
from flask_jwt_extended import get_jwt, get_jwt_identity, create_access_token, set_access_cookies
from datetime import datetime, timezone, timedelta
from flask import Response, jsonify
from errors import HttpError
from flask_jwt_extended import JWTManager


app = Flask(__name__)
api = Api(app, doc="/api/v1/docs/")
jwt = JWTManager(app)

app.config["JWT_SECRET_KEY"] = "secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = JWT_ACCESS_TOKEN_EXPIRES
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = JWT_REFRESH_TOKEN_EXPIRES
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = True

api.add_namespace(auth_ns, path="/api/v1/auth")
api.add_namespace(user_ns, path="/api/v1/users")

jwt_redis_blocklist = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header: dict, jwt_payload: dict):
    """
    Проверка, находится ли токен в блок-листе
    """
    jti = jwt_payload["jti"]

    return jwt_redis_blocklist.get(jti) is not None


@app.errorhandler(HttpError)
def error_headler(err: HttpError):
    """
    Обработчик ошибок
    """
    http_responce = jsonify({"error": err.message})
    http_responce.status_code = err.status_code
    logger.error(f"Ошибка {err.status_code}: {err.message}")
    return http_responce


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
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)
        return response

    except (RuntimeError, KeyError):
        return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
