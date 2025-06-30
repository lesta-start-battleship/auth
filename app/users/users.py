from flask_restx import Resource
from typing import Dict, List
from errors import HttpError
from extensions import jwt_redis_blocklist
from flask_jwt_extended import (
    get_jwt_identity, get_jwt, jwt_required,
    unset_access_cookies, unset_refresh_cookies
)
from flask import make_response, request
from sqlalchemy.exc import SQLAlchemyError
from config import logger, JWT_ACCESS_BLOCKLIST
from database.models import UserBase

from users.namespace import user_ns
from users.schemas import (
    error_response,
    get_user_response,
    get_users_list_request,
    get_users_list_response,
    update_user_request,
    update_user_response
)
from users.services import get_user_by_id, get_users, update_user, delete_user


class BaseResource(Resource):
    """
    Базовый класс для обработки общих функций
    """

    @property
    def user_id(self) -> int:
        """
        Получение id пользователя из JWT токена

        :return: id пользователя
        """
        return int(get_jwt_identity())

    def check_permission(self, user_id: int) -> None:
        """
        Проверка доступа к ресурсу

        :param user_id: id пользователя
        :return: None
        """
        if self.user_id != user_id:
            self.handle_error(HttpError, "Permission denied", 403)

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


@user_ns.route("/<int:user_id>")
class UserResource(BaseResource):
    """
    Класс для получения, обновления и удаления пользователя
    """
    @user_ns.doc(
        responses={
            200: ("User was found", get_user_response),
            401: ("Unauthorized", error_response),
            404: ("User not found", error_response),
            500: ("Internal server error", error_response)
        },
        description="Get user by id",
    )
    @jwt_required()
    async def get(self, user_id: int) -> UserBase | HttpError:
        """
        Получение пользователя по id

        :param user_id: id пользователя
        :return: UserBase | HttpError
        """
        self.check_permission(user_id)
        try:
            user = await get_user_by_id(user_id)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            return make_response(user, 200)

        except SQLAlchemyError:
            logger.error(f"Ошибка при получении пользователя c id: {user_id}")
            self.handle_error(HttpError, "Internal server error", 500)

    @user_ns.expect(update_user_request)
    @user_ns.doc(
        responses={
            200: ("User data was updated", update_user_response),
            400: ("No user data provided", error_response),
            401: ("Unauthorized", error_response),
            404: ("User not found", error_response),
            500: ("Internal server error", error_response)
        },
        description="Update user by id",
    )
    @jwt_required()
    async def patch(self, user_id: int) -> UserBase | HttpError:
        """
        Обновление пользователя по id

        :param user_id: id пользователя
        :return: UserBase | HttpError
        """
        self.check_permission(user_id)
        user_data = request.json
        if not user_data:
            self.handle_error(HttpError, "No user data provided", 400)
        try:    
            user = await update_user(user_id, **user_data)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            return make_response(user, 200)

        except SQLAlchemyError:
            logger.error(
                f"Ошибка при обновлении пользователя c id: {user_id} и"
                f"с данными: {user_data}"
            )
            self.handle_error(HttpError, "Internal server error", 500)

    @user_ns.doc(
        responses={
            204: "User deleted successfully",
            401: ("Unauthorized", error_response),
            404: ("User not found", error_response),
            500: ("Internal server error", error_response)
        },
        description="Delete user by id",
    )
    @jwt_required()
    async def delete(self, user_id: int) -> bool | HttpError:
        """
        Удаление пользователя по id

        :param user_id: id пользователя
        :return: bool | HttpError
        """
        self.check_permission(user_id)
        try:
            user = await delete_user(user_id)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            return make_response("User deleted successfully", 204)

        except SQLAlchemyError:
            logger.error(f"Ошибка при удалении пользователя c id: {user_id}")
            self.handle_error(HttpError, "Internal server error", 500)


@user_ns.route("/")
class GetUsersListResource(BaseResource):
    """
    Класс для получения списка пользователей
    """
    @user_ns.expect(get_users_list_request)
    @user_ns.doc(
        responses={
            200: ("List of users was fetched", get_users_list_response),
            401: ("Unauthorized", error_response),
            400: ("No user IDs provided", error_response),
            404: ("Users not found", error_response),
            500: ("Internal server error", error_response)
        },
        description="Get users by ids",
    )
    @jwt_required()
    async def get(self) -> List[UserBase] | HttpError:
        """
        Получение списка пользователей по id

        :return: List[UserBase] | HttpError
        """
        user_ids = request.args.getlist("user_ids", type=int)
        if not user_ids:
            self.handle_error(HttpError, "No users IDs provided", 400)
        try:
            users = await get_users(user_ids)
            if users is None:
                self.handle_error(HttpError, "Users not found", 404)

            return make_response({"users": users}, 200)

        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            self.handle_error(HttpError, "Internal server error", 500)


@user_ns.route("/logout/")
class LogoutUserResource(BaseResource):
    @user_ns.doc(
        responses={
            200: "Access token revoked",
            401: ("Unauthorized", error_response),
            500: ("Internal server error", error_response)
        },
        description="Logout a user",
        security=[{"JWT": []}]
    )
    @jwt_required()
    def delete(self) -> Dict[str, str] | HttpError:
        """
        Выход пользователя

        :return: Dict[str, str] | HttpError
        """
        jti = get_jwt()["jti"]
        jwt_redis_blocklist.set(jti, "", ex=JWT_ACCESS_BLOCKLIST)
        unset_access_cookies()
        unset_refresh_cookies()
        return make_response({"message": "Access token revoked"}, 200)