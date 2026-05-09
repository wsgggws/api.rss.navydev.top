from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import User  # noqa
from app.services.database import Base


class VisitLog(Base):
    __tablename__ = "visit_log"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    referer: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    visit_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VisitCountCache(Base):
    __tablename__ = "visit_count_cache"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)  # single row, id=1
    total_count: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RSSFeed(Base):
    __tablename__ = "rss_feed"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    last_fetched: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ORM 关系
    user_subscriptions = relationship("UserRSS", back_populates="rss_feed", cascade="all, delete-orphan")
    articles = relationship("RSSArticle", back_populates="rss_feed", cascade="all, delete-orphan")


class UserRSS(Base):
    __tablename__ = "user_rss"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    rss_id: Mapped[UUID] = mapped_column(ForeignKey("rss_feed.id", ondelete="CASCADE"))
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)

    user = relationship("User", back_populates="rss_subscriptions")
    rss_feed = relationship("RSSFeed", back_populates="user_subscriptions")


class RSSArticle(Base):
    __tablename__ = "rss_article"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rss_id: Mapped[UUID] = mapped_column(ForeignKey("rss_feed.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, comment="Original description from RSS feed")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_md: Mapped[str | None] = mapped_column(Text, comment="Article summary in Markdown format")
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    view_count: Mapped[int] = mapped_column(default=0)

    rss_feed = relationship("RSSFeed", back_populates="articles")
