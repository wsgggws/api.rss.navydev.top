from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss import VisitCountCache, VisitLog
from app.services.database import get_db

router = APIRouter(prefix="/api/v1/visit", tags=["Visit"])


async def get_or_create_cache(db: AsyncSession) -> VisitCountCache:
    result = await db.execute(select(VisitCountCache).where(VisitCountCache.id == 1))
    cache = result.scalar_one_or_none()
    if not cache:
        cache = VisitCountCache(id=1, total_count=0)
        db.add(cache)
        await db.flush()
    return cache


@router.post("/track")
async def track_visit(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """记录一次访问"""
    visit_dt = datetime.now(timezone.utc)

    log = VisitLog(
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
        path=request.url.path if request.url else None,
        visit_dt=visit_dt,
    )
    db.add(log)

    cache = await get_or_create_cache(db)
    cache.total_count += 1
    cache.updated_at = visit_dt

    total = cache.total_count
    await db.commit()

    return {"total_visits": total}


@router.get("/count")
async def get_visit_count(
    db: AsyncSession = Depends(get_db),
):
    """获取总访问次数（从缓存表读取，快速）"""
    cache = await get_or_create_cache(db)
    return {"total_visits": cache.total_count}