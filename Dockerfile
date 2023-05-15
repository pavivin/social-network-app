FROM python:3.11-slim

ENV PIP_DEFAULT_TIMEOUT=100 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml .
COPY poetry.lock .

RUN pip install poetry
RUN poetry install --no-root --no-ansi --no-interaction

COPY . .
