import re
from asyncio import Semaphore

from openai import AsyncOpenAI

from celery_app.constants import PROMPT
from celery_app.util import logger
from settings import settings

async_client: AsyncOpenAI | None = None


def get_async_client() -> AsyncOpenAI:
    """Create the SDK client only when AI summarization is actually enabled."""
    global async_client
    if async_client is None:
        async_client = AsyncOpenAI(base_url=settings.ai.BASE_URL, api_key=settings.ai.API_KEY)
    return async_client


def build_summary_messages(article: dict) -> list[dict[str, str]]:
    """Build an explicit boundary between editor instructions and untrusted article text."""
    title = str(article.get("title") or "未提供标题").strip()
    content = str(article.get("summary_md") or "").strip()
    return [
        {"role": "system", "content": PROMPT["SYSTEM"]},
        {"role": "user", "content": PROMPT["USER"].format(title=title, content=content)},
    ]


def normalize_summary(content: str | None) -> str:
    """Remove an accidental outer Markdown fence without touching code blocks inside the summary."""
    normalized = (content or "").strip()
    if re.match(r"^```(?:markdown|md)?\s*(?:\n|\r\n)", normalized, flags=re.IGNORECASE) and re.search(
        r"(?:\n|\r\n)```\s*$", normalized
    ):
        normalized = re.sub(r"^```(?:markdown|md)?\s*(?:\n|\r\n)", "", normalized, count=1, flags=re.IGNORECASE)
        normalized = re.sub(r"(?:\n|\r\n)```\s*$", "", normalized, count=1)
    return normalized.strip()


async def sem_async_chat(article: dict, semaphore: Semaphore | None = None):
    limiter = semaphore or Semaphore(10)
    async with limiter:
        return await async_chat(article)


async def async_chat(article: dict) -> dict:
    if not article or not article.get("summary_md") or not settings.ai.API_KEY:
        return article

    params = {
        "model": settings.ai.MODEL,
        "messages": build_summary_messages(article),
        "temperature": settings.ai.TEMPERATURE,
        "max_tokens": settings.ai.MAX_TOKENS,
        "timeout": 60,
    }
    try:
        response = await get_async_client().chat.completions.create(**params)
        summary = normalize_summary(response.choices[0].message.content)
        if summary:
            article["summary_md"] = summary
        else:
            logger.warning("LLM returned an empty summary for article %s", article.get("title") or article.get("link"))
    except Exception as exc:
        logger.error("Failed to summarize article %s: %s", article.get("link") or article.get("title"), exc, exc_info=True)
    return article
