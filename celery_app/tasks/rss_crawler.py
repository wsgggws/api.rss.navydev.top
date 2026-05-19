import asyncio
import re
from typing import Dict, List

import aiohttp
import feedparser
import html2text
from aiohttp.client import ClientTimeout
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from app.models.rss import RSSArticle
from celery_app import celery_app
from celery_app.llm import sem_async_chat
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

            articles = await fetch_articles(entries)
            articles = md_articles(articles)
            articles = await enhance_articles(articles)
            await save_articles_to_db(session, rss_id, articles)
    except Exception as e:
        logger.error(f"Error in do_one_feed_logic for {rss_id} ({url}): {e}")
    else:
        logger.info(f"successful do_one_feed_logic for {rss_id} ({url})")


def md_articles(articles: List[Dict]) -> List[Dict]:
    for article in articles:
        html = article.pop("article_html") or ""
        if not html:
            article["summary_md"] = ""
            article["image_url"] = None
            continue
        markdown = html2text.html2text(html)
        article["summary_md"] = markdown
        article["image_url"] = extract_first_image(html)
    return articles


async def enhance_articles(articles: List[Dict]) -> List[Dict]:
    semaphore = asyncio.Semaphore(10)  # 限制并发数
    tasks = [sem_async_chat(article, semaphore) for article in articles or []]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    result = []
    for item in raw_results:
        if isinstance(item, Exception):
            logger.error("Article download exception: %s", item)
            continue
        result.append(item)
    return result


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
                "published_at": parse_date(str(entry.get("published") or "")),
            }
        )
    return entries


async def _async_download(entry, session, semaphore):
    async with semaphore:
        url = entry.get("link") or ""
        try:
            async with session.get(url, headers=HEADERS, timeout=ClientTimeout(total=settings.RSS_TIMEOUT)) as response:
                if response.status == 200:
                    entry["article_html"] = await response.text()
                else:
                    entry["article_html"] = ""
                    logger.warning("%s status %s", url, response.status)
        except Exception as exc:
            logger.error("Download failed %s → %s", url, exc)
        return entry


async def fetch_articles(entries):
    semaphore = asyncio.Semaphore(10)  # 限制并发数
    async with aiohttp.ClientSession() as session:
        tasks = [_async_download(entry, session, semaphore) for entry in entries or []]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        articles = []
        for item in raw_results:
            if isinstance(item, Exception):
                logger.error("Article download exception: %s", item)
                continue
            articles.append(item)
        return articles


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


def extract_first_image(html: str) -> str | None:
    """从 HTML 中提取第一张图片的 URL"""
    if not html:
        return None
    img_patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]
    for pattern in img_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None
