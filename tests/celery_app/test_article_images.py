from celery_app.tasks.rss_crawler import absolutize_html_image_sources, extract_first_image, md_articles

ARTICLE_URL = "https://example.com/posts/2026/article.html"


def test_absolutize_html_image_sources_resolves_relative_urls():
    html = '<p>Before</p><img alt="Chart" src="../images/chart.png"><p>After</p>'

    assert 'src="https://example.com/posts/images/chart.png"' in absolutize_html_image_sources(html, ARTICLE_URL)


def test_extract_first_image_prefers_og_cover_and_resolves_its_url():
    html = """
    <html>
      <head><meta property="og:image" content="/covers/article.jpg"></head>
      <body><img src="/icons/logo.png"></body>
    </html>
    """

    assert extract_first_image(html, ARTICLE_URL) == "https://example.com/covers/article.jpg"


def test_md_articles_produces_renderable_image_urls():
    articles = [
        {
            "link": ARTICLE_URL,
            "article_html": '<article><h1>Title</h1><img alt="Diagram" src="./diagram.png"></article>',
        }
    ]

    [article] = md_articles(articles)

    assert "![Diagram](https://example.com/posts/2026/diagram.png)" in article["summary_md"]
    assert article["image_url"] == "https://example.com/posts/2026/diagram.png"
