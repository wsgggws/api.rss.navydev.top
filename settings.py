from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    URL: str = "postgresql+asyncpg://user:password@localhost:5432/newsdb"
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_TIMEOUT: int = 15
    POOL_RECYCLE: int = 1800
    POOL_PRE_PING: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="DB_",
    )


class RedisSettings(BaseSettings):
    URL: str = ""
    HOST: str = "localhost"
    PORT: int = 6379
    BROKER_NUM: int = 1
    BACKEND_NUM: int = 2

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="REDIS_",
    )


class AISettings(BaseSettings):
    BASE_URL: str = "https://api.deepseek.com"
    API_KEY: Optional[str] = None
    MODEL: str = "deepseek-v4-flash"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.1

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="LLM_",
    )


class Settings(BaseSettings):
    APP_ENV: str = "local"

    DEBUG: bool = False

    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60
    RSS_TIMEOUT: float = 15.0
    RSS_LIMITER: int = 5
    RSS_TIME_UNIT: str = "minute"
    CELERY_BEAT_MINUTES: int = 2  # 本地调试，部署时建议设置环境变量的值为 15 ~ 60

    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"  # noqa

    db: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    ai: AISettings = AISettings()

    # TODO, 这里还需要查文档，如何避免重复配置变量
    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未知变量
    )


settings = Settings()
