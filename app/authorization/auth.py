from flask import make_response, request, Blueprint, jsonify
from flask.views import MethodView
from typing import Dict
from config import logger
from errors import HttpError
from decorators import with_session
from signals import registration_user_signal
from extensions import confirm_code_redis

from authorization.services import get_user_by_username, create_user

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.models import UserBase

from werkzeug.security import check_password_hash

from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies, get_jwt_identity,
    jwt_required, get_jwt
)

from authorization.schemas import (
    validate_schema,
    UserRegRequest,
    UserLoginRequest,
    RefreshTokenRequest
)


auth_blueprint = Blueprint("Auth", __name__)


class BaseAuthView(MethodView):
    """
    Базовый класс для обработки общих функций
    """

    def _access_token(self, user: UserBase) -> str:
        """
        Создание access токена

        :param user: объект пользователя
        :return: str
        """
        return create_access_token(
            identity=str(user.id),
            additional_claims={
                "username": user.username,
                "role": user.role.value,
                "is_active": user.is_active
            }
        )

    def _refresh_token(self, user: UserBase) -> str:
        """
        Создание refresh токена

        :param user: объект пользователя
        :return: str
        """
        return create_refresh_token(
            identity=str(user.id),
            additional_claims={
                "username": user.username,
                "role": user.role.value,
                "is_active": user.is_active
            }
        )

    def handle_error(
        self,
        error: type(Exception),
        message: str,
        status_code: int
    ) -> HttpError:
        """
        Обработка ошибок

        :param error: тип ошибки
        :param message: сообщение об ошибке
        :param status_code: код статуса
        :return: HttpError
        """
        raise HttpError(status_code, message)

    def handle_validation_errors(self, error_validation_data):
        """
        Обработка ошибок валидации

        :param error_validation_data: данные ошибки валидации
        :return: HttpError
        """
        raise HttpError(
            400,
            f"{error_validation_data[0]['msg']}"
        )


class RegistrationView(BaseAuthView):
    """
    Класс для регистрации нового пользователя
    """

    @with_session
    def post(self, session_db: Session) -> Dict[str, str] | HttpError:
        """
        Регистрация нового пользователя

        :param user_data: данные пользователя в формате json
        :return: Dict[access_token: str, refresh_token: str] | HttpError
        """
        validate_data = validate_schema(UserRegRequest, **request.json)

        if isinstance(validate_data, UserRegRequest):

            if get_user_by_username(session_db, validate_data.username):
                self.handle_error(HttpError, "User already exists", 409)

            try:
                new_user = create_user(session_db, validate_data.model_dump())
                # Сигнал о регистрации пользователя для отправки email
                registration_user_signal.send(
                    self.__class__,
                    username=new_user.username,
                    email=new_user.email,
                )

                return jsonify({
                    "message": "User registered successfully, email confirmation required"
                }), 201

            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при регистрации пользователя"
                    "с данными: "
                    f"{validate_data.model_dump(exclude={'password'})}: {e}"
                )
                self.handle_error(HttpError, "Internal server error", 500)
        else:
            logger.error(
                "Ошибка валидации данных регистрации: "
                f"{validate_data.model_dump(exclude={'password'})}"
            )
            self.handle_validation_errors(
                validate_data.model_dump(exclude={'password'})
            )


class LoginView(BaseAuthView):
    """
    Класс для входа пользователя
    """

    @with_session
    def post(self, session_db: Session) -> Dict[str, str] | HttpError:
        """
        Вход пользователя

        :param user_data: username и password
        :return: Dict[access_token: str, refresh_token: str] | HttpError
        """
        validate_data = validate_schema(UserLoginRequest, **request.json)

        if isinstance(validate_data, UserLoginRequest):
            user = get_user_by_username(session_db, validate_data.username)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            try:
                if not user.is_active:
                    self.handle_error(
                        HttpError,
                        "User's email is not confirmed",
                        403
                    )

                if not check_password_hash(
                    user.h_password,
                    validate_data.password
                ):
                    self.handle_error(HttpError, "Invalid password", 401)

                access_token = self._access_token(user)
                refresh_token = self._refresh_token(user)

                response = make_response({
                    "access_token": f"Bearer {access_token}",
                    "refresh_token": f"Bearer {refresh_token}"
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

                return response

            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при входе пользователя с данными: "
                    f"{validate_data.model_dump(exclude={'password'})}: {e}"
                )
                self.handle_error(HttpError, "Internal server error", 500)
        else:
            logger.error(
                "Ошибка валидации данных входа: "
                f"{validate_data.model_dump(exclude={'password'})}"
            )
            self.handle_validation_errors(
                validate_data.model_dump(exclude={'password'})
            )

class RefreshView(BaseAuthView):

    @jwt_required(refresh=True)
    def post(self) -> Dict[str, str] | HttpError:
        """
        Обновление access токена

        :param: refresh_token из cookies или заголовка
        :return: Dict[access_token: str] | HttpError
        """
        validate_data = validate_schema(RefreshTokenRequest, **request.json)

        if isinstance(validate_data, RefreshTokenRequest):
            try:
                claims = get_jwt()
                access_token = create_access_token(
                    identity=get_jwt_identity(),
                    additional_claims={
                        "username": claims["username"],
                        "role": claims["role"],
                        "is_active": claims["is_active"]
                    }
                )

                response = make_response({
                    "access_token": f"Bearer {access_token}"
                }, 200)

                set_access_cookies(
                    response,
                    access_token,
                    max_age=60*60*24
                )

                return response

            except Exception:
                self.handle_error(HttpError, "Internal server error", 500)
        else:
            logger.error(
                f"Ошибка валидации данных обновления токена: {validate_data}"
            )
            self.handle_validation_errors(validate_data)


class ConfirmEmailView(BaseAuthView):
    """
    Класс для подтверждения email
    """

    @with_session
    def get(self, code: str, session_db: Session) -> Dict[str, str] | HttpError:
        """
        Подтверждение email

        :param code: код подтверждения
        :param session_db: сессия базы данных
        :return: Dict[str, str] | HttpError
        """

        username = confirm_code_redis.get(code)
        
        if not username:
            self.handle_error(HttpError, "Invalid code or code expired", 400)

        try:
            user = get_user_by_username(session_db, username)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            if user.is_active:
                self.handle_error(HttpError, "User already confirmed", 409)

            user.is_active = True
            session_db.commit()
            session_db.refresh(user)

            access_token = self._access_token(user)
            refresh_token = self._refresh_token(user)

            response = make_response({
                "access_token": f"Bearer {access_token}",
                "refresh_token": f"Bearer {refresh_token}"
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

            return response

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при подтверждении email: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)



auth_blueprint.add_url_rule(
    "/registration/",
    view_func=RegistrationView.as_view("registration")
)
auth_blueprint.add_url_rule(
    "/login/",
    view_func=LoginView.as_view("login")
)
auth_blueprint.add_url_rule(
    "/refresh_token/",
    view_func=RefreshView.as_view("refresh")
)

auth_blueprint.add_url_rule(
    "/confirm_email/<string:code>",
    view_func=ConfirmEmailView.as_view("confirm_email")
)
