import pytest_asyncio
from httpx import AsyncClient

from tests.helper import the_third_user


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_user_in_database(client: AsyncClient):
    # 插入一个测试用户
    response = await client.post("/api/v1/user/register", json=the_third_user)
    assert response.status_code == 200
    yield
