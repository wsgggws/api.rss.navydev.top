from datetime import datetime

from dateutil.tz import tzutc

from celery_app.tasks.rss_crawler import parse_feed

# TODO 最好是使用 VCR 这类工具将每个 feed 及 articles 自动做个记录，下次跑测试时可以模拟网络请求


def test_parse_feed_with_atom():
    # atom.xml 格式
    with open("tests/data/feed/atom.xml", "r") as f:
        xml = f.read()
        result = parse_feed(xml)
        assert len(result) == 3
        assert result == [
            {
                "title": "巨头的新战场：AI 编程 IDE（暨 字节 Trae 调用 MCP 教程）",
                "link": "http://www.ruanyifeng.com/blog/2025/04/trae-mcp.html",
                "description": "一、引言 本周，我要加写一篇文章。...",
                "published_at": datetime(2025, 4, 22, 7, 8, 3, tzinfo=tzutc()),
            },
            {
                "title": "办公类 AI 初探：扣子空间",
                "link": "http://www.ruanyifeng.com/blog/2025/04/coze-space.html",
                "description": "一、AI 的风口 问问大家，AI 产品的风口是什么？...",
                "published_at": datetime(2025, 4, 21, 2, 50, 46, tzinfo=tzutc()),
            },
            {
                "title": "科技爱好者周刊（第 345 期）：HDMI 2.2 影音可能到头了",
                "link": "http://www.ruanyifeng.com/blog/2025/04/weekly-issue-345.html",
                "description": "这里记录每周值得分享的科技内容，周五发布。...",
                "published_at": datetime(2025, 4, 18, 0, 7, 46, tzinfo=tzutc()),
            },
        ]


def test_parse_feed_with_rss():
    # rss.xml 格式
    with open("tests/data/feed/rss.xml", "r") as f:
        xml = f.read()
        result = parse_feed(xml)
        assert len(result) == 12
        assert result[:3] == [
            {
                "title": "第219期 - 一艘活船",
                "link": "https://weekly.tw93.fun/posts/219-%E4%B8%80%E8%89%98%E6%B4%BB%E8%88%B9/",
                "description": "封面图拍摄于周末天气不错，走路出去闲逛，看到远处河里有一艘船，还有炊烟，走过去看了看，拍了张照片，看着是有人在里面做饭，顿时船也有了生命一样。",
                "published_at": datetime(2025, 4, 21, 0, 0, tzinfo=tzutc()),
            },
            {
                "title": "第218期 - 勾狗可爱",
                "link": "https://weekly.tw93.fun/posts/218-%E5%8B%BE%E7%8B%97%E5%8F%AF%E7%88%B1/",
                "description": "封面图拍摄于在麻车头组，人偏多，我感觉还是径山花海露营舒服，这个村里露营时候拍到的狗，非常可爱，会笑，逗了逗挺有趣。",
                "published_at": datetime(2025, 4, 14, 0, 0, tzinfo=tzutc()),
            },
            {
                "title": "第217期 - 去露个营",
                "link": "https://weekly.tw93.fun/posts/217-%E5%8E%BB%E9%9C%B2%E4%B8%AA%E8%90%A5/",
                "description": "封面图拍摄于清明节在杭州径山花海露营的照片，放假前一天购买的帐篷天幕二合一，还挺好用，简易好安装，这个地方很适合露营，人不是太多，有山有水有花有草，很舒服的。",
                "published_at": datetime(2025, 4, 7, 0, 0, tzinfo=tzutc()),
            },
        ]
