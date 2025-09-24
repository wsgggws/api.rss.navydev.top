# 第一阶段: 构建依赖环境
# FROM python:3.11-slim AS builder
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim AS builder


# 安装 Poetry
RUN python3 -m pip install --no-cache-dir poetry==2.1.0

# 设置环境变量，确保 Poetry 在项目目录创建 `.venv`
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_NO_INTERACTION=true

# 设置工作目录
WORKDIR /api.rss.navydev.top

# 复制依赖文件（避免代码变动导致重新安装所有依赖）
COPY pyproject.toml poetry.lock ./

# 安装依赖（只安装 main，不安装 dev 依赖）
RUN python3 -m poetry install --only main --no-root

# 第二阶段: 运行时环境
# FROM python:3.11-slim AS runtime
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim AS runtime

# 设置虚拟环境路径
ENV VIRTUAL_ENV=/api.rss.navydev.top/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 设置工作目录
WORKDIR /api.rss.navydev.top

# 复制 Poetry 安装的依赖（仅复制已安装的依赖，而不复制 `poetry` 本身）
COPY --from=builder /api.rss.navydev.top/.venv /api.rss.navydev.top/.venv

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8000

CMD ["sh", "./scripts/start-web.sh"]
