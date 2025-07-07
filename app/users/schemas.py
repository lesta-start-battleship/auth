import re
from pydantic import BaseModel, ValidationError, field_validator, EmailStr
from typing import List
from datetime import datetime
from database.models import Role
from config import logger


def validate_schema(schema_cls: type, **kwargs):
    try:
        check_validate = schema_cls(**kwargs)
        return check_validate
    except ValidationError as e:
        logger.error(f"Ошибка валидации данных: {e}")
        return e.errors()


class Currency(BaseModel):
    id: int
    gold: int
    guild_rage: int

    class Config:
        from_attributes = True


class GetUserResponse(BaseModel):
    id: int
    email: str
    username: str
    name: str
    surname: str
    role: str
    is_active: bool
    created_at: datetime
    currencies: Currency

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    name: str | None = None
    surname: str | None = None
    role: Role | None = None

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

    @field_validator("role")
    @classmethod
    def validate_role(cls, role):
        if not role:
            raise ValueError("Роль не введена")
        if role not in Role:
            raise ValueError("Неверная роль")
        return role


class UpdateUserResponse(GetUserResponse):
    pass


class GetUsersListRequest(BaseModel):
    user_ids: List[int]


class GetUsersListResponse(BaseModel):
    users: List[GetUserResponse]
