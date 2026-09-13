from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import celery_app.llm as llm
from celery_app.llm import async_chat, build_summary_messages, normalize_summary
from settings import settings


def test_build_summary_messages_includes_title_and_markdown_boundaries():
    messages = build_summary_messages({"title": "A useful title", "summary_md": "Body with {braces}."})

    assert messages[0]["role"] == "system"
    assert "不可信资料" in messages[0]["content"]
    assert "一至三张" in messages[0]["content"]
    assert "绝不生成、改写或猜测 URL" in messages[0]["content"]
    assert "<article_title>\nA useful title\n</article_title>" in messages[1]["content"]
    assert "<article_markdown>\nBody with {braces}.\n</article_markdown>" in messages[1]["content"]


def test_normalize_summary_removes_only_an_outer_markdown_fence():
    fenced = """```markdown
> 导读

## 核心内容

```python
print("kept")
```
```"""

    assert normalize_summary(fenced) == "> 导读\n\n## 核心内容\n\n```python\nprint(\"kept\")\n```"


def test_normalize_summary_handles_empty_response():
    assert normalize_summary(None) == ""


@pytest.mark.asyncio
async def test_async_chat_uses_ai_settings_and_normalizes_response(monkeypatch):
    completion = AsyncMock()
    completion.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="```markdown\n> 摘要\n```"))]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=completion)))
    monkeypatch.setattr(llm, "async_client", client)
    monkeypatch.setattr(settings.ai, "API_KEY", "test-key")
    monkeypatch.setattr(settings.ai, "TEMPERATURE", 0.25)
    monkeypatch.setattr(settings.ai, "MAX_TOKENS", 2048)

    article = await async_chat({"title": "标题", "summary_md": "原始正文"})

    assert article["summary_md"] == "> 摘要"
    params = completion.await_args.kwargs
    assert params["temperature"] == 0.25
    assert params["max_tokens"] == 2048
    assert "<article_title>\n标题\n</article_title>" in params["messages"][1]["content"]
