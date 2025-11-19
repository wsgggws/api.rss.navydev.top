import pytest_asyncio
from httpx import AsyncClient

from tests.helper import the_first_user, the_second_user


# module 意味着在 user 这个模块下执行一次
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_user_in_database(client: AsyncClient):
    # 插入两个个测试用户
    response = await client.post("/api/v1/user/register", json=the_first_user)
    assert response.status_code == 200
    response = await client.post("/api/v1/user/register", json=the_second_user)
    assert response.status_code == 200
    yield
