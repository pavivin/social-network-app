import uuid
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
    email: EmailStr | None
    role: User.Role
    exp: datetime | None


class CheckUserLogin(BaseModel):
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None
    city: str | None = None


class ProfileUpdateView(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    image_url: AnyUrl | None = None
    city: str | None = None
    district: str | None = None
    phone: str
    birthdate: date | None = None


class ProfileView(BaseModel):
    id: uuid.UUID | str
    first_name: str | None = None
    last_name: str | None = None
    image_url: AnyUrl | None = None
    city: str | None = None
    district: str | None = None
    birthdate: date | None = None
    relationship_type: str | None = None
    email: str


class OwnProfileView(BaseModel):
    id: uuid.UUID | str
    first_name: str | None = None
    last_name: str | None = None
    image_url: AnyUrl | None = None
    city: str | None = None
    district: str | None = None
    birthdate: date | None = None
    relationship_type: str | None = None
    email: str
    email_approved: bool = False


class UserView(BaseModel):
    id: uuid.UUID | str
    first_name: str = "unknown"
    last_name: str = "user"
    image_url: str | None


class SearchListView(BaseModel):
    users: list[UserView]


class CityListView(BaseModel):
    cities: list[str]
