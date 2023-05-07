from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel

from voices.protocol import BaseModel

from .models import User


class Token(PydanticBaseModel):
    access_token: str
    refresh_token: str


class TokenData(PydanticBaseModel):
    email: str
    role: User.UserRole
    exp: datetime | None


class UserLogin(BaseModel):
    email: str
    password: str
