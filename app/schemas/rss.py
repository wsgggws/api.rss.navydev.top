from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


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
    published_at: datetime = Field(description="Article 发布日期")
    summary_md: Optional[str] = Field(None, description="AI摘要")

    class Config:
        from_attributes = True  # 允许 Pydantic 直接从 ORM 模型转换


class RSSArticlesListResponse(BaseModel):
    items: List[RSSArticleResponse] = Field(description="Articles 列表")
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
