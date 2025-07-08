import re
from pydantic import BaseModel, field_validator, ValidationError, EmailStr
from config import logger


def validate_schema(schema_cls: type, **kwargs):
    try:
        check_validate = schema_cls(**kwargs)
        return check_validate
    except ValidationError as e:
        logger.error(f"Ошибка валидации данных: {e}")
        return e.errors()


class UserRegRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str | None = None
    surname: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        if not password:
            raise ValueError("Пароль не введен")
        if not re.match(
            r"(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z]{8,}$",
            password
        ):
            raise ValueError(
                "Неверный формат пароля, должен содержать хотя "
                "бы одну заглавную букву, одну строчную букву и одну цифру,"
                " длина не менее 8 символов"
            )
        return password


class UserLoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
