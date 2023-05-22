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
    role: User.UserRole
    exp: datetime | None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileView(BaseModel):
    first_name: str = None
    last_name: str = None
    image_url: AnyUrl | None = None
    email: EmailStr
    role: str


class UserView(BaseModel):
    first_name: str = None
    last_name: str = None
    email: EmailStr


class SearchListView(BaseModel):
    users: list[UserView]
