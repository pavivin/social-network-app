from datetime import date, datetime

from pydantic import AnyUrl, EmailStr

from voices.app.core.protocol import BaseModel

from .models import User


class Token(BaseModel):
    access_token: str
    refresh_token: str


class TokenView(BaseModel):
    access_token: str
    refresh_token: str
    rocketchat_user_id: str
    rocketchat_auth_token: str
    exp: datetime


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
    district: str | None = None
    birthdate: date | None = None


class UserView(BaseModel):
    first_name: str = "unknown"
    last_name: str = "user"
    email: EmailStr


class SearchListView(BaseModel):
    users: list[UserView]
