from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqladmin import Admin, ModelView

import voices.app.auth.controllers as auth
import voices.app.healthcheck.controllers as healthcheck
import voices.app.initiatives.controllers as initiatives
from voices import exceptions
from voices.app.auth.models import User
from voices.db.base import engine
from voices.logger import logger
from voices.protocol import Response

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.first_name, User.role]


admin.add_view(UserAdmin)

app.include_router(healthcheck.router, tags=["healthcheck"])
app.include_router(auth.router, tags=["auth"], prefix="/api")
app.include_router(initiatives.router, tags=["auth"], prefix="/api")


@app.exception_handler(Exception)
async def uvicorn_base_exception_handler(request: Request, exc: Exception):
    logger.debug(exc)
    error = exceptions.ServerError(str(exc))
    return ORJSONResponse(
        Response(
            code=error.status_code,
            message=error.message,
            body=error.payload,
            exception_class=error.__class__.__name__,
        ).dict()
    )


@app.exception_handler(exceptions.ApiException)
async def unicorn_api_exception_handler(request: Request, exc: exceptions.ApiException):
    logger.debug(str(exc))  # TODO: добавить асинхронный логер

    return ORJSONResponse(
        Response(
            code=exc.status_code,
            message=exc.message,
            body=exc.payload,
            exception_class=exc._type(),
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.debug(exc)
    error = exceptions.ValidationError(message=str(exc))
    return ORJSONResponse(
        Response(
            code=error.status_code,
            message=error.message,
            body=error.payload,
            exception_class=error._type(),
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000)
