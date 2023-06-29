from datetime import datetime

from pydantic import AnyUrl, EmailStr

from voices.protocol import BaseModel

from .models import User


class Token(BaseModel):
    access_token: str
    refresh_token: str


class TokenData(BaseModel):
    sub: str
    email: EmailStr
    role: User.Role
    exp: datetime | None


class CheckUserLogin(BaseModel):
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileView(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    image_url: AnyUrl | None = None
    city: str | None = None


class UserView(BaseModel):
    first_name: str = None
    last_name: str = None
    email: EmailStr


class SearchListView(BaseModel):
    users: list[UserView]
