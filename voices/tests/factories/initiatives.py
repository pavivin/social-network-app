import factory
from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from faker import Factory as FakerFactory
from pytest_factoryboy import register

from voices.app.initiatives.models import Comment, Initiative
from voices.db.base import sc_session
from voices.tests.factories.user import UserFactory

faker = FakerFactory.create()


@register
class InitiativeFactory(AsyncSQLAlchemyFactory):
    user = factory.SubFactory(UserFactory)
    city = "test"
    images = ["https://pbs.twimg.com/media/EaH598OWsAAoGzB.jpg"]
    category = Initiative.Category.PROBLEM
    # location = "POINT(1, 1)"
    title = factory.LazyAttribute(lambda x: faker.name())
    main_text = factory.LazyAttribute(lambda x: faker.name())

    class Meta:
        model = Initiative
        sqlalchemy_session = sc_session


@register
class CommentFactory(AsyncSQLAlchemyFactory):
    main_text = factory.LazyAttribute(lambda x: faker.name())
    user = factory.SubFactory(UserFactory)
    initiative = factory.SubFactory(InitiativeFactory)

    class Meta:
        model = Comment
        sqlalchemy_session = sc_session
