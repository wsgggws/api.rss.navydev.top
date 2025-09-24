from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

from app.middlewares import TraceIDHeaderMiddleware


def setup_middlewares(app):
    """
    最后注册的中间件最先执行（在请求进入时）
    最先注册的中间件最后执行（在响应返回时）
    2 ➝ 1 ➝ 路由处理函数 ➝ 1 ➝ 2
    """

    origins = [
        "http://localhost:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.add_middleware(TraceIDHeaderMiddleware)
    # 为每个请求创建一个 Root Span, 将 SpanContext 放入当前 Context 中
    # 供后续代码（比如 FastAPIInstrumentor、自定义中间件）访问 trace.get_current_span() 获取当前 trace 上下文。
    app.add_middleware(OpenTelemetryMiddleware)
