from pydantic import Field

from .exceptions import BadRequestError, NotFoundError
from .protocol import Response


class BadRequestResponse(Response):
    code: int = Field(BadRequestError.status_code, description="Код ответа (http-like)")
    message: str | None = Field(BadRequestError.message, description="Описание кода ответа")


class NotFoundResponse(Response):
    code: int = Field(NotFoundError.status_code, description="Код ответа (http-like)")
    message: str | None = Field(BadRequestError.message, description="Описание кода ответа")
