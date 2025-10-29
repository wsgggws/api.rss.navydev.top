#!/bin/sh
set -e

echo "🚀 Starting FastAPI application."

# 启动 FastAPI (监听 HTTP)
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
