import uuid
from datetime import date, datetime


from pydantic import AnyUrl, EmailStr
import pydantic

from voices.app.core.protocol import BaseModel, PhoneNumber

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
    user_id: str


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
    phone: PhoneNumber | None = None
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
    phone: str | None = None
    friends_count: int


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
    phone: str | None = None
    friends_count: int


class UserView(BaseModel):
    id: uuid.UUID | str
    first_name: str = "unknown"
    last_name: str = "user"
    image_url: str | None

    @pydantic.validator("image_url", pre=True)
    def prepare_public_file(cls, v: str, values):
        if not v.startswith("https://storage.yandexcloud"):
            return v
        if "min" in v:
            return v
        filename = v.split("/")[-1]
        name, file_ext = filename.split(".")
        return f"https://storage.yandexcloud.net/my-city/{name}-min.{file_ext}"


class SearchListView(BaseModel):
    users: list[UserView]


class CityListView(BaseModel):
    cities: list[str]
