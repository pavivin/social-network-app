from typing import Generic, TypeVar

import orjson
import phonenumbers
from geoalchemy2.shape import to_shape
from pydantic import BaseModel as PydanticModel
from pydantic import Field
from pydantic.generics import GenericModel as PydanticGenericModel
from pydantic.validators import strict_str_validator

from voices.config import settings

DataT = TypeVar("DataT")


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class BaseModel(PydanticModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        alias_generator = to_camel_case
        orm_mode = True
        allow_population_by_field_name = True


class Response(PydanticGenericModel, Generic[DataT]):
    """
    Базовый ответ на запрос
    """

    code: int = Field(200, description="Код ответа (http-like)")
    message: str | None = Field(description="Описание кода ответа")
    payload: DataT | None = Field(None, description="Тело ответа")
    exception_class: str | None = Field(None, description="Имя класса ошибки")

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class PaginationView(BaseModel):
    count: int = 0
    total: int = 0
    limit: int = settings.DEFAULT_PAGE_SIZE
    is_next: bool = True


class GeometryPoint(BaseModel):
    lat: float
    lon: float

    @staticmethod
    def to_str(location: dict):
        if not location:
            return None
        return f'POINT({location["lat"]} {location["lon"]})'

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return v

        shape = to_shape(v)
        return {"lat": shape.x, "lon": shape.y}


class PhoneNumber(str):
    """Phone Number Pydantic type, using google's phonenumbers"""

    @classmethod
    def __get_validators__(cls):
        yield strict_str_validator
        yield cls.validate

    @classmethod
    def validate(cls, v: str):
        v = v.strip().replace(" ", "")

        try:
            parsed_number = phonenumbers.parse(v)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValueError("invalid phone number format")

        return cls(phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164))
