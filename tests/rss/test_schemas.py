from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.rss import RSSArticleListItem


def article_payload(published_at):
    return {
        "id": uuid4(),
        "title": "An article",
        "link": "https://example.com/article",
        "description": "Original feed description.",
        "published_at": published_at,
        "image_url": "https://example.com/cover.jpg",
    }


def test_article_schema_hides_epoch_placeholder_and_keeps_image():
    article = RSSArticleListItem.model_validate(article_payload(datetime(1970, 1, 1, tzinfo=timezone.utc)))

    assert article.published_at is None
    assert article.description == "Original feed description."
    assert article.image_url == "https://example.com/cover.jpg"


def test_article_schema_keeps_real_publication_date():
    published_at = datetime(2026, 9, 13, tzinfo=timezone.utc)

    assert RSSArticleListItem.model_validate(article_payload(published_at)).published_at == published_at
