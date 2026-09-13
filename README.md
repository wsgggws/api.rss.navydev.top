# api.rss.navydev.top

[![CI](https://github.com/wsgggws/api.rss.navydev.top/actions/workflows/ci.yml/badge.svg)](https://github.com/wsgggws/api.rss.navydev.top/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/wsgggws/api.rss.navydev.top/branch/main/graph/badge.svg)](https://codecov.io/gh/wsgggws/api.rss.navydev.top)

RSS NAVY 的后端服务。项目负责 RSS 订阅管理、定时采集、文章元数据查询、用户认证和访问统计，并提供一套基于 OpenTelemetry 的可观测性环境。

- 前端：<https://rss.navydev.top/>
- 线上 API：<https://api.rss.navydev.top/>
- 本地 Swagger UI：<http://127.0.0.1:8000/docs>

## 核心能力

- 使用 FastAPI 提供异步 REST API
- 使用 PostgreSQL 和 SQLAlchemy 存储订阅源、文章、用户及访问记录
- 使用 Celery Beat 定时调度，Celery Worker 抓取并解析 RSS Feed
- 使用 `aiohttp`、Feedparser 和 Parsel 提取文章标题、链接、日期与 description
- 将缺失或 `1970` Unix Epoch 占位日期规范化为 `null`
- 支持 JWT 认证、RSS 接口限流和推荐订阅源
- 支持 OpenTelemetry、Prometheus、Grafana、Tempo 和 Loki
- 使用 Pytest、Ruff 和覆盖率报告保障代码质量

## 技术栈

| 类别 | 技术 |
| --- | --- |
| 语言与包管理 | Python 3.12、uv |
| Web API | FastAPI、Uvicorn、Pydantic |
| 数据库 | PostgreSQL 16、SQLAlchemy、asyncpg |
| 异步任务 | Celery、Redis |
| RSS 解析 | Feedparser、aiohttp、Parsel |
| 认证与限流 | JWT、Argon2、SlowAPI |
| 可观测性 | OpenTelemetry、Prometheus、Grafana、Tempo、Loki |
| 测试与检查 | Pytest、pytest-asyncio、Ruff、Codecov |
| 部署 | Docker Compose、Nginx |

## 工作流程

```text
Celery Beat
    -> 分发需要更新的订阅源
    -> Worker 获取并解析 Feed
    -> 写入 PostgreSQL
    -> FastAPI 向前端提供文章列表与详情
```

服务不会下载、转换或存储文章正文。API 返回 Feed 中的文章元数据和原始 `link`，由前端浏览器直接加载来源页面。这减少了采集耗时、存储占用和内容失真，也让读者看到作者发布的原始排版。

## 项目结构

```text
app/
├── models/       # SQLAlchemy 数据模型
├── routes/       # FastAPI 路由
├── schemas/      # Pydantic 请求与响应模型
├── services/     # 数据库和认证服务
└── utils/        # 限流、校验和日志工具
celery_app/
├── tasks/        # RSS 调度、抓取和入库任务
└── config.py     # Celery 配置
config/           # PostgreSQL、Nginx 与可观测性配置
scripts/          # 本地运行、测试和部署脚本
tests/            # API、抓取器、模型和工具测试
```

## 环境要求

- Python `>=3.12,<3.13`
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16
- Redis 6.2 或兼容版本
- Docker 与 Docker Compose，推荐用于数据库、Redis 和完整服务栈

安装依赖：

```bash
uv sync
```

## 环境变量

本地脚本从 `.env.local` 加载变量，Docker Compose 使用 `.env.docker` 和 `.env`。不要把真实密钥提交到仓库。

常用配置示例：

```dotenv
APP_ENV=local
SECRET_KEY=replace-with-a-random-secret

DB_URL=postgresql+asyncpg://user:password@localhost:5432/newsdb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=15
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_BROKER_NUM=1
REDIS_BACKEND_NUM=2

RSS_TIMEOUT=15
RSS_LIMITER=5
RSS_TIME_UNIT=minute
CELERY_BEAT_MINUTES=15
```

## 本地运行

启动 FastAPI 及 PostgreSQL：

```bash
make local-run
```

服务默认运行于 <http://127.0.0.1:8000>。

启动和停止定时采集任务：

```bash
make local-celery-start
make local-celery-stop
```

也可以启动完整 Docker Compose 环境：

```bash
make docker-run
make docker-stop
```

Docker Compose 会启动 Web API、Celery Worker、Celery Beat、PostgreSQL、Redis、Nginx，以及可选的完整可观测性组件。首次启动前需要创建 Compose 使用的外部网络并准备环境文件。

## API

主要接口如下，完整请求与响应结构以 Swagger UI 为准。

| 方法 | 路径 | 认证 | 用途 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/user/register` | 否 | 注册用户 |
| `POST` | `/api/v1/user/token` | 否 | 获取访问令牌 |
| `GET` | `/api/v1/user/me` | 是 | 获取当前用户 |
| `PUT` | `/api/v1/user/me` | 是 | 更新当前用户 |
| `POST` | `/api/v1/rss/subscribe` | 是 | 添加订阅源 |
| `DELETE` | `/api/v1/rss/unsubscribe/{rss_id}` | 是 | 取消订阅 |
| `GET` | `/api/v1/rss/subscriptions` | 否 | 获取可用订阅源 |
| `GET` | `/api/v1/rss/subscriptions/{rss_id}/articles` | 否 | 获取订阅源文章 |
| `GET` | `/api/v1/rss/subscriptions/{rss_id}/articles/{article_id}` | 否 | 获取文章详情并增加阅读次数 |
| `GET` | `/api/v1/rss/recommended` | 否 | 获取推荐订阅源 |
| `POST` | `/api/v1/visit/track` | 否 | 记录站点访问 |
| `GET` | `/api/v1/visit/count` | 否 | 获取累计访问次数 |

现有数据库中的旧正文/摘要列不再由应用读取或写入，可以在完成数据库备份后通过单独迁移删除。当前变更不执行破坏性数据库操作。

文档地址：

- Swagger UI：`/docs`
- ReDoc：`/redoc`
- OpenAPI JSON：`/openapi.json`

## 测试与代码检查

测试脚本会启动独立的 PostgreSQL 测试实例，并读取 `.env.ci`：

```bash
# 全部测试
make test

# 传递 Pytest 参数
make test ARGS="-vv -s"

# 运行指定测试
make test ARGS="tests/celery_app/test_rss_crawler_fun.py -q"
```

运行静态检查：

```bash
uv run ruff check .
```

## 可观测性

使用 OpenTelemetry Instrumentation 启动 API：

```bash
make local-otel-run
```

相关服务与默认端口：

| 服务 | 端口 | 用途 |
| --- | --- | --- |
| Grafana | `3000` | 指标、日志和链路看板 |
| Prometheus | `9090` | Metrics 存储与查询 |
| Tempo | `3200` | Traces 存储与查询 |
| Loki | `3100` | Logs 存储与查询 |
| OTLP gRPC | `4317` | 遥测数据接收 |

## License

[MIT](./LICENSE)
