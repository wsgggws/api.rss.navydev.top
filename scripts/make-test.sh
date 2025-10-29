#!/usr/bin/env bash

set -euo pipefail

echo "📦 关闭旧容器..."
docker compose down test-db || true

echo "🐘 启动 PostgreSQL test-db 数据库..."
docker compose up -d test-db

echo "🔧 加载 CI 环境变量 (.env.ci)..."
set -a
source .env.ci
set +a

# 如果没有传参，则直接跑 pytest
if [ $# -eq 0 ]; then
  echo "🧪 运行所有测试 (默认)..."
  uv run pytest
else
  echo "🧪 运行 pytest with args: $*"
  uv run pytest "$@"
fi

echo "🧼 删除旧 <none> 镜像..."
docker images --filter "dangling=true" -q | xargs -r docker rmi
