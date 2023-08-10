from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqladmin import Admin, ModelView

import voices.app.auth.controllers as auth
import voices.app.friends.controllers as friends
import voices.app.healthcheck.controllers as healthcheck
import voices.app.initiatives.controllers as initiatives
import voices.app.storage.controllers as storage
from voices.app.auth.models import User
from voices.app.core import exceptions
from voices.app.core.protocol import Response
from voices.app.initiatives.models import Initiative
from voices.db.base import engine
from voices.logger import logger
from voices.mongo import mongo_client
from voices.mongo.models import Survey, SurveyAnswer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=mongo_client.voices,
        document_models=[Survey, SurveyAnswer],
    )
    yield


app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None, lifespan=lifespan)

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


class InitiativeAdmin(ModelView, model=Initiative):
    column_list = [
        Initiative.category,
        Initiative.title,
        Initiative.main_text,
        Initiative.created_at,
        Initiative.from_date,
        Initiative.to_date,
        Initiative.city,
        Initiative.likes_count,
        Initiative.comments_count,
        Initiative.user,
    ]


admin.add_view(UserAdmin)
admin.add_view(InitiativeAdmin)

app.include_router(healthcheck.router, tags=["healthcheck"])
app.include_router(auth.router, tags=["auth"], prefix="/api")
app.include_router(initiatives.router, tags=["initiatives"], prefix="/api")
app.include_router(storage.router, tags=["storage"], prefix="/api")
app.include_router(friends.router, tags=["friends"], prefix="/api")


# TODO: add sentry
@app.exception_handler(Exception)
async def uvicorn_base_exception_handler(request: Request, exc: Exception):
    logger.error(exc)
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
    logger.debug(str(exc))

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


@app.exception_handler(HTTPException)
async def validation_http_exception_handler(request: Request, exc: HTTPException):
    logger.error(exc)
    error = exceptions.UnauthorizedError(message=str(exc))
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
