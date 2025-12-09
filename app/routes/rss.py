from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import RSSInvalidException, RSSNotFoundException, RSSSubscribeRepeatException, UserBannedException
from app.models.rss import RSSArticle, RSSFeed, UserRSS
from app.models.user import User
from app.schemas.rss import (
    RSSArticleResponse,
    RSSArticlesListResponse,
    RSSRecommendedListResponse,
    RSSSubscribeRequest,
    RSSSubscribeResponse,
    RSSSubscribesListResponse,
)
from app.services.auth import get_current_user
from app.services.database import get_db
from app.utils.limiter import rss_limiter
from app.utils.validator import get_rss_title
from settings import settings

router = APIRouter(prefix="/api/v1/rss", tags=["RSS"])


@router.post("/subscribe", response_model=RSSSubscribeResponse)
@rss_limiter.limit(f"{settings.RSS_LIMITER}/{settings.RSS_TIME_UNIT}")
async def subscribe_rss(
    request: Request,
    data: RSSSubscribeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """订阅一个新的RSS源"""
    user_id = user.id
    # 检查 RSSFeed 是否已存在
    result = await db.execute(select(RSSFeed).where(RSSFeed.url == str(data.url)))
    rss = result.scalar_one_or_none()

    if not rss:
        # 是不是有效的 Feed url, 并拿到 title
        title = await get_rss_title(data.url)
        if not title:
            raise RSSInvalidException
        rss = RSSFeed(url=str(data.url), title=title)
        db.add(rss)
        await db.commit()
        await db.flush()
        await db.refresh(rss)

    # 这里需要先记录下值，由于下一次会再执行数据库操作
    rss_id = rss.id
    rss_title = rss.title
    rss_url = rss.url

    # 是否已经订阅
    result = await db.execute(select(UserRSS).where(UserRSS.user_id == user_id, UserRSS.rss_id == rss_id))
    existing = result.scalar_one_or_none()
    if existing:
        raise RSSSubscribeRepeatException

    subscription = UserRSS(user_id=user_id, rss_id=rss_id)
    db.add(subscription)
    await db.commit()
    await db.flush()
    return {"id": rss_id, "title": rss_title, "url": rss_url, "message": "success"}


@router.get("/subscriptions", response_model=RSSSubscribesListResponse)
async def get_subscriptions(
    limit: int = Query(10, gt=0),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前用户已订阅的RSS源列表"""
    total = await db.scalar(select(func.count()).select_from(UserRSS).where(UserRSS.user_id == user.id))

    result = await db.execute(
        select(RSSFeed)
        .join(UserRSS, RSSFeed.id == UserRSS.rss_id)
        .where(UserRSS.user_id == user.id)
        .offset(offset)
        .limit(limit)
    )
    feeds = result.scalars().all()
    return {
        "items": [{"id": f.id, "url": f.url, "title": f.title} for f in feeds],
        "total": total,
    }


@router.get("/subscriptions/{rss_id}/articles", response_model=RSSArticlesListResponse)
async def get_articles_by_subscription(
    rss_id: UUID = Path(...),
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取指定订阅源下的文章列表"""
    # 验证该订阅是否属于该用户
    result = await db.scalar(
        select(func.count())
        .select_from(RSSFeed)
        .join(UserRSS, RSSFeed.id == UserRSS.rss_id)
        .where(UserRSS.user_id == user.id, UserRSS.rss_id == rss_id)
    )
    if result == 0:
        return {"items": [], "total": 0}

    # 查询总数
    total = await db.scalar(select(func.count()).select_from(RSSArticle).where(RSSArticle.rss_id == rss_id))

    # 分页查询文章
    result = await db.execute(
        select(RSSArticle)
        .where(RSSArticle.rss_id == rss_id)
        .order_by(RSSArticle.published_at.desc())
        .offset(offset)
        .limit(limit)
    )
    articles = result.scalars().all()

    return {
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "link": a.link,
                "published_at": a.published_at,
            }
            for a in articles
        ],
        "total": total,
    }


@router.get("/subscriptions/{rss_id}/articles/{article_id}", response_model=RSSArticleResponse)
async def get_article_detail(
    rss_id: UUID = Path(...),
    article_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取指定文章的详细信息"""
    # 校验该订阅是否属于当前用户
    has_access = await db.scalar(select(UserRSS).where(UserRSS.user_id == user.id, UserRSS.rss_id == rss_id))
    if not has_access:
        raise UserBannedException

    # 查找文章
    result = await db.execute(select(RSSArticle).where(RSSArticle.id == article_id, RSSArticle.rss_id == rss_id))
    article = result.scalar_one_or_none()

    if not article:
        raise RSSNotFoundException

    return {
        "id": article.id,
        "title": article.title,
        "link": article.link,
        "published_at": article.published_at,
        "summary_md": article.summary_md,
    }


@router.delete("/unsubscribe/{rss_id}")
async def unsubscribe_rss(
    rss_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """取消订阅一个RSS源"""
    result = await db.execute(
        delete(UserRSS).where(UserRSS.user_id == user.id, UserRSS.rss_id == rss_id).returning(UserRSS.id)
    )
    deleted = result.scalar_one_or_none()
    if not deleted:
        raise RSSNotFoundException
    await db.commit()
    return {"message": "取消订阅成功"}


@router.get("/recommended", response_model=RSSRecommendedListResponse)
async def get_recommended_rss(
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """获取推荐的RSS源列表（基于所有用户的订阅）"""
    # 查询总数：统计所有被至少一个用户订阅过的 RSS 源数量
    total_query = (
        select(func.count(func.distinct(RSSFeed.id)))
        .select_from(RSSFeed)
        .join(UserRSS, RSSFeed.id == UserRSS.rss_id)
    )
    total = await db.scalar(total_query)

    # 分页查询：获取所有被订阅过的 RSS 源，按订阅数量排序
    feeds_query = (
        select(RSSFeed, func.count(UserRSS.id).label("subscriber_count"))
        .join(UserRSS, RSSFeed.id == UserRSS.rss_id)
        .group_by(RSSFeed.id)
        .order_by(func.count(UserRSS.id).desc())  # 按订阅数量降序排列
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(feeds_query)
    feeds = result.all()

    return {
        "items": [
            {
                "id": feed.id,
                "title": feed.title or "未知标题",
                "description": None,  # RSSFeed 模型中没有 description 字段，可以后续扩展
                "url": feed.url,
            }
            for feed, _ in feeds
        ],
        "total": total or 0,
    }
