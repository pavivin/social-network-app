from datetime import datetime

from voices.protocol import BaseModel

from .models import User


class Token(BaseModel):
    access_token: str
    refresh_token: str


class TokenData(BaseModel):
    sub: str
    email: str
    role: User.UserRole
    exp: datetime | None


class UserLogin(BaseModel):
    email: str
    password: str


class ProfileUpdateView(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str
    role: str


class ProfileView(BaseModel):
    email: str
    role: str


class UserView(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str


class SearchListView(BaseModel):
    users: list[UserView]
