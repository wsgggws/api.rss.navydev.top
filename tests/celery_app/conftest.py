import logging

import pytest

from app.models.rss import RSSFeed
from app.services.database import AsyncSession
from tests.helper import test_feeds


def pytest_configure():
    logging.getLogger("vcr").setLevel(logging.WARNING)


@pytest.fixture(scope="function", autouse=True)
async def async_test_db():
    feed1 = RSSFeed(**test_feeds[0])
    feed2 = RSSFeed(**test_feeds[1])
    async with AsyncSession() as async_session:
        async_session.add(feed1)
        async_session.add(feed2)
        await async_session.commit()
        await async_session.flush()
        await async_session.refresh(feed1)
        await async_session.refresh(feed2)
    yield
