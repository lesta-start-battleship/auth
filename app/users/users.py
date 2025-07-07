from typing import Dict, List

from errors import HttpError

from extensions import jwt_redis_blocklist

from config import logger, JWT_ACCESS_BLOCKLIST

from decorators import with_session

# from signals import change_username_signal

from flask import make_response, request, jsonify, Blueprint
from flask.views import MethodView
from flask_jwt_extended import (
    get_jwt_identity, get_jwt, jwt_required,
    unset_access_cookies, unset_refresh_cookies
)

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


from database.models import UserBase

from users.services import (
    get_full_user_by_id,
    get_users,
    update_user,
    delete_user
)
from users.schemas import (
    validate_schema,
    GetUserResponse,
    UpdateUserRequest,
    GetUsersListRequest,
    GetUsersListResponse
)


user_blueprint = Blueprint("Users", __name__)


class BaseUserView(MethodView):
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

    def check_permission(self, user_id: int) -> None | HttpError:
        """
        Проверка доступа к ресурсу

        :param user_id: id пользователя
        :return: None | HttpError
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

    def handle_validation_errors(self, error_validation_data):
        """
        Обработка ошибок валидации

        :param error_validation_data: данные ошибки валидации
        :return: HttpError
        """
        raise HttpError(
            400,
            f"{error_validation_data[0]['msg'].split(',')[1]}"
        )


class UserView(BaseUserView):
    """
    Класс для получения, обновления и удаления пользователя
    """

    @with_session
    @jwt_required()
    def get(self, session_db: Session, user_id: int) -> UserBase | HttpError:
        """
        Получение пользователя по id

        :param session_db: сессия базы данных
        :param user_id: id пользователя
        :return: UserBase | HttpError
        """
        self.check_permission(user_id)
        try:
            user = get_full_user_by_id(session_db, user_id)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            response_data = GetUserResponse.model_validate(user)

            if isinstance(response_data, GetUserResponse):
                return jsonify(response_data.model_dump()), 200

            else:
                logger.error(
                    f"Ошибка валидации данных {response_data}"
                    f"от пользователя: {self.user_id}"
                )
                self.handle_error(HttpError, "Error returning user data", 500)

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении пользователя c id: {user_id}: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)

    @with_session
    @jwt_required()
    def patch(self, session_db: Session, user_id: int) -> UserBase | HttpError:
        """
        Обновление пользователя по id

        :param session_db: сессия базы данных
        :param user_id: id пользователя
        :return: UserBase | HttpError
        """
        self.check_permission(user_id)
        user_data = validate_schema(UpdateUserRequest, **request.json)
        if isinstance(user_data, UpdateUserRequest):

            try:
                user = update_user(
                    session_db,
                    user_id,
                    **user_data.model_dump(exclude_none=True)
                )
                if not user:
                    self.handle_error(HttpError, "User not found", 404)

                response_data = GetUserResponse.model_validate(user)
                # if user_data.username:
                #     change_username_signal.send(
                #         self.__class__,
                #         user_id=user_id,
                #         username=user_data.username
                #     )
                if isinstance(response_data, GetUserResponse):
                    return jsonify(response_data.model_dump()), 200

                else:
                    logger.error(
                        f"Ошибка валидации данных {response_data}"
                        f"от пользователя: {self.user_id}"
                    )
                    self.handle_error(
                        HttpError,
                        "Error returning user data",
                        500
                    )

            except SQLAlchemyError as e:
                logger.error(
                    f"Ошибка при обновлении пользователя c id: {user_id} и"
                    f"с данными: {user_data}: {e}"
                )
                self.handle_error(HttpError, "Internal server error", 500)

        else:
            logger.error(
                f"Ошибка валидации данных {user_data}"
                f"от пользователя: {self.user_id}"
            )
            self.handle_validation_errors(user_data)

    @with_session
    @jwt_required()
    def delete(self, session_db: Session, user_id: int) -> bool | HttpError:
        """
        Удаление пользователя по id

        :param user_id: id пользователя
        :return: bool | HttpError
        """
        self.check_permission(user_id)
        try:
            user = delete_user(session_db, user_id)
            if not user:
                self.handle_error(HttpError, "User not found", 404)

            return make_response({"message": "User deleted successfully"}, 204)

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при удалении пользователя c id: {user_id}: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)


class GetUsersListResource(BaseUserView):
    """
    Класс для получения списка пользователей
    """

    @with_session
    @jwt_required()
    def get(self, session_db: Session) -> List[UserBase] | HttpError:
        """
        Получение списка пользователей по id

        :param session_db: сессия базы данных
        :param user_ids: список id пользователей
        :return: List[UserBase] | HttpError
        """
        user_ids = request.args.getlist("user_ids", type=int)
        validate_users_ids = validate_schema(
            GetUsersListRequest,
            user_ids=user_ids
        )
        if isinstance(validate_users_ids, GetUsersListRequest):

            try:
                users = get_users(session_db, validate_users_ids.user_ids)

                response_data = validate_schema(
                    GetUsersListResponse,
                    users=users
                )
                if isinstance(response_data, GetUsersListResponse):
                    return jsonify(response_data.model_dump()), 200

                else:
                    logger.error(
                        f"Ошибка валидации данных {response_data}"
                        f"от пользователя: {self.user_id}"
                    )
                    self.handle_error(
                        HttpError,
                        "Error returning user data",
                        500
                    )

            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении списка пользователей: {e}")
                self.handle_error(HttpError, "Internal server error", 500)


class LogoutUserResource(BaseUserView):

    @jwt_required()
    def post(self) -> Dict[str, str] | HttpError:
        """
        Выход пользователя

        :return: Dict[str, str] | HttpError
        """
        try:
            jti = get_jwt()["jti"]
            jwt_redis_blocklist.set(jti, "", ex=JWT_ACCESS_BLOCKLIST)

            response = make_response({"message": "Пользователь вышел"}, 200)
            unset_access_cookies(response)
            unset_refresh_cookies(response)

            logger.info(f"Access token revoked for user {self.user_id}")
            return response

        except Exception as e:
            logger.error(f"Ошибка при выходе пользователя: {e}")
            self.handle_error(HttpError, "Internal server error", 500)


user_blueprint.add_url_rule(
    "/<int:user_id>",
    view_func=UserView.as_view("user")
)
user_blueprint.add_url_rule(
    "/",
    view_func=GetUsersListResource.as_view("get_users_list")
)
user_blueprint.add_url_rule(
    "/logout/",
    view_func=LogoutUserResource.as_view("logout")
)
