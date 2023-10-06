from pathlib import Path
from typing import Any, Mapping, Optional

from pydantic import BaseSettings, PostgresDsn, validator

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name = "voices-backend"
    tasks_name = "voices-tasks"

    DEBUG: bool = False

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DATABASE: str
    POSTGRES_TEST_DATABASE: str = ""
    DATABASE_URL: PostgresDsn = ""
    TEST_DATABASE_URL: PostgresDsn = ""
    ALEMBIC_DATABASE_URL: PostgresDsn = ""

    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_REPLICA_SET: str = "rs0"

    SERVER_PORT: int = 8000
    SERVER_HOST: str = "0.0.0.0"

    REDIS_URL: str = "redis://localhost:6379"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_BACKEND_URL: str = "redis://localhost:6379/1"

    AUTH_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRES: int = 30 * 60
    REFRESH_TOKEN_EXPIRES = 60 * 60 * 24 * 30

    AUTH_PUBLIC_KEY: Path = BASE_DIR / "secret.pub"
    AUTH_PRIVATE_KEY: Path = BASE_DIR / "secret"
    AUTH_PUBLIC_KEY_DATA: str = None
    AUTH_PRIVATE_KEY_DATA: str = None

    DEFAULT_PAGE_SIZE = 20
    ACTUAL_PAGE_SIZE = 5  # TODO: rename (actuals or actual feed)

    RAW_OBSCENE_WORDS_FILE = "obscene_words.txt"
    NORMALIZED_OBSCENE_WORDS_FILE = "normalized_words.txt"

    FILE_ENCODING = "UTF-8"
    # FIREBASE
    FIREBASE_SECRETS = "./voices_firebase_secrets.json"

    ALLOWED_PHOTO_TYPES = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_VIDEO_TYPES = {"webp", "gif", "mp4", "mov", "aiff"}
    ALLOWED_MODEL_TYPES = {"gltf", "glb"}
    ALLOWED_UPLOAD_TYPES = ALLOWED_PHOTO_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_MODEL_TYPES

    FILE_MAX_SIZE_MB: int = 10
    FILE_MAX_SIZE_KB: int = 1024 * 1024 * FILE_MAX_SIZE_MB

    ROCKETCHAT_WEBSOCKET: str
    ROCKETCHAT_USER: str
    ROCKETCHAT_PASSWORD: str
    ROCKETCHAT_URL: str

    SENTRY_DSN: str

    DEFAULT_CITY: str = "Ярославль"

    MAIL_SENDER_EMAIL: str = "no-reply@voices-city.ru"
    MAIL_SENDER_PASSWORD: str = "eBG-zC3-wc3-Nbw"
    MAIL_SENDER_DOMAIN: str = "smtp.timeweb.ru"  # mail.hosting.reg.ru
    MAIL_SENDER_PORT: int = 25

    @validator("AUTH_PRIVATE_KEY_DATA", pre=True)
    def prepare_private_file(cls, v: Optional[str], values: Mapping[str, Any]):
        if v and isinstance(v, str):
            return v
        result = open(values["AUTH_PRIVATE_KEY"], mode="r").read()
        return result

    @validator("AUTH_PUBLIC_KEY_DATA", pre=True)
    def prepare_public_file(cls, v: Optional[str], values: Mapping[str, Any]):
        if v and isinstance(v, str):
            return v
        result = open(values["AUTH_PUBLIC_KEY"], mode="r").read()
        return result

    @validator("DATABASE_URL", pre=True)
    def assemble_postgres_db_url(cls, v: Optional[str], values: Mapping[str, Any]) -> str:
        if v and isinstance(v, str):
            return v

        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                user=values["POSTGRES_USER"],
                password=values["POSTGRES_PASSWORD"],
                host=values["POSTGRES_HOST"],
                port=str(values["POSTGRES_PORT"]),
                path=f'/{values["POSTGRES_DATABASE"]}',
            )
        )

    @validator("ALEMBIC_DATABASE_URL", pre=True)
    def assemble_alembic_database_url(cls, v: Optional[str], values: Mapping[str, Any]) -> str:
        if v and isinstance(v, str):
            return v

        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg2",
                user=values["POSTGRES_USER"],
                password=values["POSTGRES_PASSWORD"],
                host=values["POSTGRES_HOST"],
                port=str(values["POSTGRES_PORT"]),
                path=f'/{values["POSTGRES_DATABASE"]}',
            )
        )

    @validator("TEST_DATABASE_URL", pre=True)
    def assemble_test_postgres_url(cls, v: Optional[str], values: Mapping[str, Any]) -> str:
        if not values.get("POSTGRES_TEST_DATABASE"):
            return ""
        if v and isinstance(v, str):
            return v

        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                user=values["POSTGRES_USER"],
                password=values["POSTGRES_PASSWORD"],
                host=values["POSTGRES_HOST"],
                port=str(values["POSTGRES_PORT"]),
                path=f'/{values["POSTGRES_TEST_DATABASE"]}',
            )
        )

    class Config:
        env_file = ".env"


settings = Settings()
