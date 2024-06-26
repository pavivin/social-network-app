# Social App

There is social app that I worked with.

Stack:

FastAPI, PostgreSQL, MongoDB, Redis, Celery, Pytest


Note: It's a big project, I wrote this alone. I did not have much time to write the cleanest code.

I'm going to improve some parts to create some useful template.

What it consist of:

- Tests (I have some)
    - Factory for tests
- Pre-commit linting
- Simple profanity filter (enough for test)
- Docker, deploy overall (now it's commented)
- Working notifications
- Suitable admin-panel in django
- Bunch of useful scripts
- Integration with Rocketchat
- Async code
- S3 integration
- Sentry SDK
- Using uuidv7 to better indexing

What can be improved:

- write more tests
- CI: linting, test-coverage, security
- using out-of-box fastapi-filters
- using out-of-box fastapi-pagination
- using graph databases for friends
- move secret out of repo
- advanced profanity filter

## Dependencies install

```bash
pip install poetry
poetry install
```

## Add dependency

```bash
poetry add
```

## pre-commit install

```bash
pip install pre-commit
pre-commit install
```

## Run pre-commit

```bash
pre-commit run -a
```

## Run celery worker

```bash
celery -A voices.broker worker -l info
```

## Run celery-beat

```bash
celery -A voices.broker beat -l info
```
