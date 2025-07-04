from pydantic import BaseModel


class GetUserCurrenciesResponse(BaseModel):
    gold: int
    guild_rage: int

    class Config:
        from_attributes = True


class UpdateUserCurrenciesRequest(BaseModel):
    gold: int | None = None
    guild_rage: int | None = None


class UpdateUserCurrenciesResponse(GetUserCurrenciesResponse):
    pass
