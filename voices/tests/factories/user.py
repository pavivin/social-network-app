import factory
from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from faker import Factory as FakerFactory
from pytest_factoryboy import register

from voices.app.auth.models import User
from voices.auth.hash import get_password_hash
from voices.db.base import sc_session

faker = FakerFactory.create()


@register
class UserFactory(AsyncSQLAlchemyFactory):
    first_name = factory.LazyAttribute(lambda x: faker.name())
    last_name = factory.LazyAttribute(lambda x: faker.name())
    email = factory.LazyAttribute(lambda x: faker.email())
    role = "USER"
    hashed_password = factory.LazyAttribute(lambda x: get_password_hash("password"))

    class Meta:
        model = User
        sqlalchemy_session = sc_session
