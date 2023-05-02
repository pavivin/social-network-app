from typing import Mapping


class ApiException(Exception):
    """
    Base class for API exceptions
    """

    status_code: int = 500
    message: str = "Упс! Что-то пошло не так ;("

    def __init__(self, message: str | None = None, payload: Mapping | None = None):
        self.message = message or self.message
        self.payload = payload

    def to_json(self) -> Mapping:
        return {"code": self.status_code, "message": self.message, "payload": self.payload}


class ServerError(ApiException):
    status_code = 500
    message = "Упс! Что-то пошло не так ;("


class NotFoundError(ApiException):
    status_code = 404
    message = "Not Found"


class BadRequestError(ApiException):
    status_code = 400


class ForbiddenError(ApiException):
    status_code = 403
    message = "Forbidden"


class UpgradeRequiredError(ApiException):
    status_code = 426
    message = "Upgrade required"
