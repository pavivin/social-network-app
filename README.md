# Запуск

## Установка зависимостей

```bash
pip install poetry
poetry install
```

## Добавление зависимости

```bash
poetry add
```

## Установка pre-commit

```bash
pip install pre-commit
pre-commit install
```

## Запуск pre-commit вручную

```bash
pre-commit run -a
```

## Запуск celery

```bash
celery -A voices.broker worker -l info
```

## Запуск celery-beat

```bash
celery -A voices.broker beat -l info
```

## Тесты

Для тестов используется pytest и pytest-factoryboy

Factoryboy представляет собой автоматическое создание моделей

Вызывать готовые модели и factory можно как фикстуры в тестах.
