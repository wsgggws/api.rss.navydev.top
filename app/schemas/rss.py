from datetime import datetime
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, HttpUrl


def reject_epoch_placeholder(value: Optional[datetime]) -> Optional[datetime]:
    """Treat Unix-epoch feed dates as missing instead of exposing 1970 to clients."""
    if value is not None and value.year <= 1970:
        return None
    return value


PublishedAt = Annotated[Optional[datetime], AfterValidator(reject_epoch_placeholder)]


class RSSSubscribeRequest(BaseModel):
    url: HttpUrl = Field(description="要订阅的RSS源的URL")
    title: Optional[str] = Field(None, description="RSS源的标题 (可选, 如果未提供将尝试自动获取)")
    notify_enabled: bool = Field(True, description="是否为此订阅开启通知 (默认为True)")


class RSSSubscribeResponse(BaseModel):
    id: UUID = Field(description="成功订阅后RSS源在数据库中的唯一标识符")
    url: HttpUrl = Field(description="已订阅的RSS源的URL")
    title: Optional[str] = Field(None, description="已订阅的RSS源的标题")
    message: Optional[str] = Field("success", description="操作结果消息 (例如 'success')")

    class Config:
        from_attributes = True  # 允许 Pydantic 直接从 ORM 模型转换


class RSSSubscribesListResponse(BaseModel):
    items: List[RSSSubscribeResponse] = Field(description="订阅 RSS 详情列表")
    total: int = Field(description="用户订阅 RSS 的总数量")


class RSSArticleResponse(BaseModel):
    id: UUID = Field(description="成功订阅后RSS源在数据库中的唯一标识符")
    title: str = Field(description="Article origin title")
    link: HttpUrl = Field(description="Article origin link")
    published_at: PublishedAt = Field(None, description="Article 发布日期")
    view_count: int = Field(0, description="文章阅读次数")
    image_url: Optional[str] = Field(None, description="文章封面图片")

    class Config:
        from_attributes = True


class RSSArticleListItem(BaseModel):
    id: UUID
    title: str
    link: HttpUrl
    description: Optional[str] = None
    published_at: PublishedAt = None
    view_count: int = 0
    image_url: Optional[str] = None


class RSSArticlesListResponse(BaseModel):
    items: List[RSSArticleListItem] = Field(description="Articles 列表")
    total: int = Field(description="Articles 的总数量")


class RSSRecommendedItem(BaseModel):
    id: UUID = Field(description="RSS源在数据库中的唯一标识符")
    title: str = Field(description="RSS源的标题")
    description: Optional[str] = Field(None, description="RSS源的描述")
    url: HttpUrl = Field(description="RSS源的URL")

    class Config:
        from_attributes = True


class RSSRecommendedListResponse(BaseModel):
    items: List[RSSRecommendedItem] = Field(description="推荐的 RSS 源列表")
    total: int = Field(description="推荐的 RSS 源总数量")
