from flask import make_response, request
from flask_restx import Resource
from typing import Dict
from authorization.namespace import auth_ns

from config import logger
from authorization.services import get_user_by_username, create_user
from errors import HttpError

from sqlalchemy.exc import SQLAlchemyError

from database.models import UserBase

from werkzeug.security import check_password_hash

from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies, get_jwt_identity,
    jwt_required
)

from authorization.schemas import (
    user_reg_request,
    user_reg_response,
    error_response,
    user_login_request,
    user_login_response
)


class BaseResource(Resource):
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
                "role": user.role,
                "currencies": user.currencies # условнно связанное поле с таблицей валюты
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
                "role": user.role,
                "currencies": user.currencies # условнно связанное поле с таблицей валюты
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


@auth_ns.route("/registration/")
class RegistrationView(BaseResource):
    """
    Класс для регистрации нового пользователя
    """
    @auth_ns.expect(user_reg_request)
    @auth_ns.doc(
        responses={
            201: ("User registered successfully", user_reg_response),
            400: ("User already exists", error_response),
            500: ("Internal server error", error_response)
        },
        description="Registration a new user",
    )
    async def post(self) -> Dict[str, str] | HttpError:
        """
        Регистрация нового пользователя

        :param user_data: данные пользователя в формате json
        :return: Dict[access_token: str, refresh_token: str] | HttpError
        """
        logger.info(
            f"Для регистрации пользователя приняты данные: {request.json}"
        )
        user_data = request.json

        if await get_user_by_username(user_data["username"]): # проверка по мылу
            self.handle_error(HttpError, "User already exists", 400)

        try:
            new_user = await create_user(user_data)
            access_token = self._access_token(new_user)
            refresh_token = self._refresh_token(new_user)
            response = make_response({
                "access_token": access_token,
                "refresh_token": refresh_token
            }, 201)

            set_access_cookies(
                response,
                access_token,
                httponly=True,
                secure=True
            )
            set_refresh_cookies(
                response,
                refresh_token,
                httponly=True,
                secure=True,
                max_age=60*60*24*7
            )

            return response

        except SQLAlchemyError:
            logger.error(
                f"Ошибка при регистрации пользователя с данными: {user_data}"
            )
            self.handle_error(HttpError, "Internal server error", 500)


@auth_ns.route("/login/")
class LoginView(BaseResource):
    """
    Класс для входа пользователя
    """
    @auth_ns.expect(user_login_request)
    @auth_ns.doc(
        responses={
            200: ("Login was successful", user_login_response),
            400: ("Invalid password", error_response),
            404: ("User not found", error_response),
            500: ("Internal server error", error_response)
        },
        description="Login a user",
    )
    async def post(self) -> Dict[str, str] | HttpError:
        """
        Вход пользователя

        :param user_data: username и password
        :return: Dict[access_token: str, refresh_token: str] | HttpError
        """
        logger.info(f"Для входа пользователя приняты данные: {request.json}")
        user_data = request.json

        user = await get_user_by_username(user_data["username"]) # проверка по мылу 
        if not user:
            self.handle_error(HttpError, "User not found", 404)

        try:
            if not check_password_hash(user.password, user_data["password"]):
                self.handle_error(HttpError, "Invalid password", 400)

            access_token = self._access_token(user)
            refresh_token = self._refresh_token(user)

            response = make_response({
                "access_token": access_token,
                "refresh_token": refresh_token
            }, 200)

            set_access_cookies(
                response,
                access_token,
                httponly=True,
                secure=True
            )
            set_refresh_cookies(
                response,
                refresh_token,
                httponly=True,
                secure=True,
                max_age=60*60*24*7
            )

            return response

        except SQLAlchemyError:
            logger.error(
                f"Ошибка при входе пользователя с данными: {user_data}"
            )
            self.handle_error(HttpError, "Internal server error", 500)


@auth_ns.route("/refresh_token/")
class RefreshView(BaseResource):
    @auth_ns.expect(user_reg_request)
    @auth_ns.doc(
        responses={
            200: ("User logged in successfully", user_reg_response),
            400: ("User already exists", error_response),
            500: ("Internal server error", error_response)
        },
        description="Login a user",
        security=[{"JWT": []}]
    )
    @jwt_required(refresh=True)
    async def post(self) -> Dict[str, str] | HttpError:
        """
        Обновление access токена

        :param: refresh_token из cookies или заголовка Authorization
        :return: Dict[access_token: str] | HttpError
        """
        try:
            identity = get_jwt_identity()
            access_token = self._access_token(identity)

            response = make_response({
                "access_token": access_token
            }, 200)

            set_access_cookies(
                response,
                access_token,
                httponly=True,
                secure=True
            )

            return response

        except Exception:
            self.handle_error(HttpError, "Internal server error", 500)
            