import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.main import app
from app.services.database import Base, engine
from settings import settings

assert settings.db.URL.endswith("test_newsdb")


# https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops
# https://pypi.org/project/pytest-async-sqlalchemy/
# or poolclass = NullPool when create_async_engine
@pytest.fixture(scope="function")
def event_loop():
    """Create a fresh event loop for each test (function scope).

    This avoids pytest-asyncio ScopeMismatch errors when session-scoped
    fixtures try to access function-scoped internals. Using a new
    event loop per test is the recommended, simple approach for these
    tests.
    """
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """为每个测试初始化数据库（每个测试函数执行一次），避免 session-scoped async fixture 引发 ScopeMismatch。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print(f"\n创建所有表: {settings.db.URL}")
    yield
    async with engine.begin() as conn:
        print(f"\n丢弃所有表: {settings.db.URL}")
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
def generate_token():
    def _generate_token(username="wsgggws", token_type="valid_token"):
        payload = {
            "sub": username,
            "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        if token_type == "expired_token":
            payload["exp"] = datetime.now(tz=timezone.utc) - timedelta(minutes=1)  # 生成过期 token
        elif token_type == "invalid_token":
            return "invalid.token.string"
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return _generate_token


@pytest.fixture(scope="session")
def vcr_config():
    return {
        # Replace the Authorization request header with "DUMMY" in cassettes
        "filter_headers": [("authorization", "DUMMY")],
        "cassette_library_dir": "tests/data/cassettes",
        "decode_compressed_response": True,
        "log": None,
        # 在测试中允许重新录制（在某些环境 cassette 可能需更新）
        # 可根据 CI/本地需求改回 'once' 或 'none'
        # "record_mode": "all",
        "record_mode": "none",
    }
