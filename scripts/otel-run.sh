#!/usr/bin/env bash
set -euo pipefail

echo "📦 关闭旧容器..."
docker compose down
echo "📦 启动所有服务..."
docker compose up -d

echo "🔧 加载 env.local 与 OTel 环境变量..."
set -a
source .env.local
source .otel.env
set +a

echo "🔭 启动带 OpenTelemetry 的 FastAPI 服务..."
opentelemetry-instrument uvicorn app.main:app
