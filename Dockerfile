# 第一阶段: 构建依赖环境
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.12-slim AS builder

# 安装 uv（比 pip/poetry 更快）
RUN pip install --no-cache-dir uv

# 设置工作目录
WORKDIR /api.rss.navydev.top

# 复制依赖文件（缓存优化：先复制 pyproject 和锁文件）
COPY pyproject.toml uv.lock ./

# 直接在系统环境安装依赖（不使用 .venv）
# --frozen: 严格使用锁文件版本
# --system: 安装到系统 site-packages
ENV UV_INDEX_URL=https://pypi.org/simple
RUN uv sync --frozen --no-dev

# 第二阶段: 运行环境
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.12-slim AS runtime

# 设置工作目录
WORKDIR /api.rss.navydev.top

# 从 builder 复制系统级已安装依赖（site-packages）
# Python 安装目录一般为 /usr/local/lib/python3.12/
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["sh", "./scripts/start-web.sh"]
