from pydantic import ValidationError

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from flask.views import MethodView
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity


from errors import HttpError
from config import logger
from decorators import with_session

from currencies.services import get_user_currencies, update_user_currencies
from currencies.schemas import (
    GetUserCurrenciesResponse,
    UpdateUserCurrenciesResponse,
    UpdateUserCurrenciesRequest
)


currencies_blueprint = Blueprint("Currencies", __name__)


class BaseCurrencyView(MethodView):
    """
    Базовый класс для работы с валютами
    """

    @property
    def user_id(self) -> int:
        """
        Получение id пользователя из JWT токена

        :return: id пользователя
        """
        return int(get_jwt_identity())

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


class CurrenciesView(BaseCurrencyView):
    """
    Класс для работы с валютами
    """

    @with_session
    @jwt_required()
    def get(self, session_db: Session):
        """
        Получение списка валют
        """
        try:
            user_currencies = get_user_currencies(
                user_id=self.user_id,
                session_db=session_db
            )
            if not user_currencies:
                self.handle_error(HttpError, "User not found", 404)

            validation_response = GetUserCurrenciesResponse.model_validate(
                user_currencies
            )
            return jsonify(validation_response.model_dump()), 200

        except ValidationError as e:
            logger.error(
                f"Ошибка валидации данных {user_currencies}"
                f"для пользователя: {self.user_id}: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при получении валют пользователя c id: "
                f"{self.user_id}: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)

    @with_session
    @jwt_required()
    def patch(self, session_db: Session):
        """
        Обновление списка валют
        """
        try:
            user_currencies_data = UpdateUserCurrenciesRequest(**request.json)
            if isinstance(user_currencies_data, UpdateUserCurrenciesRequest):
                user_currencies = update_user_currencies(
                    user_id=self.user_id,
                    session_db=session_db,
                    **user_currencies_data.model_dump(exclude_none=True)
                )
                if not user_currencies:
                    self.handle_error(HttpError, "User not found", 404)

                validation_response = (
                    UpdateUserCurrenciesResponse.model_validate(
                        user_currencies
                    )
                )
                return jsonify(validation_response.model_dump()), 200

            else:
                logger.error(
                    f"Ошибка валидации данных {user_currencies_data}"
                    f"от пользователя: {self.user_id}"
                )
                self.handle_validation_errors(user_currencies_data)

        except ValidationError as e:
            logger.error(
                f"Ошибка валидации данных {validation_response}"
                f"для пользователя: {self.user_id}: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)

        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при обновлении валют пользователя c id: "
                f"{self.user_id}: {e}"
            )
            self.handle_error(HttpError, "Internal server error", 500)


currencies_blueprint.add_url_rule(
    "/",
    view_func=CurrenciesView.as_view("currencies_view")
)
