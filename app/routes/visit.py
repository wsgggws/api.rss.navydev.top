from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rss import VisitCountCache, VisitLog
from app.services.database import get_db

router = APIRouter(prefix="/api/v1/visit", tags=["Visit"])


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

    row = await db.execute(select(VisitCountCache.total_count).where(VisitCountCache.id == 1))
    current = row.scalar()

    if current is None:
        db.add(VisitCountCache(id=1, total_count=1, updated_at=visit_dt))
        total = 1
    else:
        await db.execute(
            update(VisitCountCache)
            .where(VisitCountCache.id == 1)
            .values(total_count=current + 1, updated_at=visit_dt)
        )
        total = current + 1

    await db.commit()
    return {"total_visits": total}


@router.get("/count")
async def get_visit_count(
    db: AsyncSession = Depends(get_db),
):
    """获取总访问次数（从缓存表读取，快速）"""
    row = await db.execute(select(VisitCountCache.total_count).where(VisitCountCache.id == 1))
    total = row.scalar()
    return {"total_visits": total if total is not None else 0}