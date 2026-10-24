#!/usr/bin/env bash
set -euo pipefail

echo "📦 关闭旧容器 web celery-worker celery-beat."
docker compose down web celery-worker celery-beat || true

echo "📦 加载环境变量 .env.docker .env"
set -a
source .env.docker
source .env
set +a

echo "🚀 启动容器 web celery-worker celery-beat."
docker compose up --build web celery-worker celery-beat -d

echo "🔄 重新加载 nginx 配置（让 conf.d 变更生效）."
if docker inspect nginx-ssl >/dev/null 2>&1; then
  docker exec nginx-ssl nginx -s reload
else
  echo "未找到 nginx-ssl 容器；由中央 nginx 处理反向代理，跳过 reload。"
fi

echo "🧼 删除旧 <none> 镜像..."
docker images --filter "dangling=true" -q | xargs -r docker rmi
