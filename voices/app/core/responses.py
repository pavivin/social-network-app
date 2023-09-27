from pydantic import Field

from .exceptions import BadRequestError, ForbiddenError, NotFoundError
from .protocol import Response


class BadRequestResponse(Response):
    code: int = Field(BadRequestError.status_code, description="Код ответа (http-like)")
    message: str | None = Field(BadRequestError.message, description="Описание кода ответа")


class NotFoundResponse(Response):  # TODO: auto creating response class from error
    code: int = Field(NotFoundError.status_code, description="Код ответа (http-like)")
    message: str | None = Field(NotFoundError.message, description="Описание кода ответа")


class ForbiddenResponse(Response):
    code: int = Field(ForbiddenError.status_code, description="Код ответа (http-like)")
    message: str | None = Field(ForbiddenError.message, description="Описание кода ответа")
