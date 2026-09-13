import logging

from dateutil import parser as date_parser
from parsel import Selector
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from settings import settings

logger = logging.getLogger(__name__)


def get_celery_async_session():
    engine = create_async_engine(
        settings.db.URL,
        pool_size=settings.db.POOL_SIZE,  # 连接池大小，默认值通常是 5；设置过大会浪费资源
        max_overflow=settings.db.MAX_OVERFLOW,  # 超出 pool_size 后允许的最大连接溢出数
        pool_timeout=settings.db.POOL_TIMEOUT,  # 从连接池获取连接的最大等待时间（秒），超时会报错
        pool_recycle=settings.db.POOL_RECYCLE,  # 连接最大复用时间（秒），避免连接被数据库关闭
        pool_pre_ping=settings.db.POOL_PRE_PING,  # 每次使用连接前是否做“ping”检测，防止连接已失效
    )

    CeleryAsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)
    return CeleryAsyncSessionMaker


def parse_date(date_str: str = ""):
    """将 RSS 中的时间字符串解析为 datetime"""
    if not date_str:
        return None
    try:
        # feedparser 的 parsed_parsed 不一定有 → 使用 dateutil 兜底
        parsed_date = date_parser.parse(date_str)
        # Some feeds use the Unix epoch as a placeholder for a missing date.
        return parsed_date if parsed_date.year > 1970 else None
    except Exception as e:
        logger.error(f"Failed to parse date: {date_str}, error: {e}")
        return None


def parse_description(description: str = ""):
    return Selector(description).xpath("//text()[normalize-space(.) != '']").extract_first()
