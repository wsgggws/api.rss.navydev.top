from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from settings import settings

# 创建异步的 SQLAlchemy 引擎。
# 在测试数据库中使用 NullPool（不复用连接），以避免不同测试用例使用不同 event loop 时
# 出现 "got Future attached to a different loop" 的错误。
engine_kwargs = {}
if settings.db.URL.endswith("test_newsdb"):
    # 测试环境：不使用连接池，确保每次连接在当前事件循环中创建/关闭
    engine_kwargs["poolclass"] = NullPool
else:
    # 非测试环境使用配置的连接池参数
    engine_kwargs.update(
        {
            "pool_size": settings.db.POOL_SIZE,
            "max_overflow": settings.db.MAX_OVERFLOW,
            "pool_timeout": settings.db.POOL_TIMEOUT,
            "pool_recycle": settings.db.POOL_RECYCLE,
            "pool_pre_ping": settings.db.POOL_PRE_PING,
        }
    )

engine = create_async_engine(settings.db.URL, **engine_kwargs)
AsyncSession = async_sessionmaker(engine)


# 获取异步数据库会话
async def get_db():
    async with AsyncSession() as session:
        yield session  # 提供 session


async def init_db():
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


# 所有被继承表 Base
class Base(DeclarativeBase):
    pass
