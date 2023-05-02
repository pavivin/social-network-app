import factory
from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from faker import Factory as FakerFactory
from pytest_factoryboy import register

from vizme.app.healthcheck.models import Author

faker = FakerFactory.create()


@register
class AuthorFactory(AsyncSQLAlchemyFactory):
    name = factory.LazyAttribute(lambda x: faker.name())

    class Meta:
        model = Author
