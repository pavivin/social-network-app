import pytest
from factories import AuthorFactory


@pytest.mark.asyncio
async def test_factory(async_session):
    author = await AuthorFactory.create()
    author
