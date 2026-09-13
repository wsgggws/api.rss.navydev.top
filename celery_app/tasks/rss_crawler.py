import asyncio
from typing import Dict, List

import aiohttp
import feedparser
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from app.models.rss import RSSArticle
from celery_app import celery_app
from celery_app.util import get_celery_async_session, logger, parse_date, parse_description
from settings import settings

HEADERS = {"User-Agent": settings.USER_AGENT}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def do_one_feed(self, rss_id: str, feed_url: str):
    asyncio.run(do_one_feed_logic(rss_id, feed_url))


async def do_one_feed_logic(rss_id: str, url: str):
    try:
        celery_session_marker = get_celery_async_session()
        async with celery_session_marker() as session:
            feed_html = await fetch_feed(url)
            if not feed_html:
                logger.error(f"Failed to fetch feed from {url}")
                return

            entries = parse_feed(html=feed_html)
            logger.info(f"Parsed {len(entries)} entries from feed")

            exist_urls = await get_exist_urls(session, rss_id)
            entries = discard_exists_entries(entries, exist_urls)
            logger.info(f"Found {len(entries)} new entries to process")

            await save_articles_to_db(session, rss_id, entries)
    except Exception as e:
        logger.error(f"Error in do_one_feed_logic for {rss_id} ({url}): {e}")
    else:
        logger.info(f"successful do_one_feed_logic for {rss_id} ({url})")


async def get_exist_urls(session, rss_id) -> set:
    exist_links = set()
    articles = await session.execute(select(RSSArticle).where(RSSArticle.rss_id == rss_id))
    for article in articles.scalars().all():
        exist_links.add(article.link)
    return exist_links


def discard_exists_entries(entries, exist_urls) -> List:
    result = []
    unique_urls = set(exist_urls or [])
    for entry in entries or []:
        link = entry.get("link") or ""
        if link not in unique_urls:
            result.append(entry)
            unique_urls.add(link)
    return result


async def fetch_feed(url):
    logger.info(f"Fetching RSS feed: {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as e:
            logger.info(f"Error fetching RSS ({url}): {e}")
            return


def parse_feed(html):
    entries = []
    feed = feedparser.parse(html)
    for entry in feed.entries:
        description = parse_description(str(entry.get("summary") or entry.get("description") or ""))
        entries.append(
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "description": description,
                "published_at": parse_date(
                    str(entry.get("published") or entry.get("updated") or entry.get("created") or "")
                ),
            }
        )
    return entries


async def save_articles_to_db(session, rss_id, articles: List[Dict]):
    for article in articles or []:
        new_article = RSSArticle(rss_id=rss_id, **article)
        session.add(new_article)
    try:
        await session.commit()
        logger.info(f"Saved {len(articles)} new articles to database.")
    except IntegrityError:
        logger.warning("IntegrityError during saving articles: skiping")
        await session.rollback()
