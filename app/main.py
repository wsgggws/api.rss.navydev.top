# import sentry_sdk
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from app.error_handlers import setup_exception_handlers
from app.extentions import setup_extentions
from app.middleware_handlers import setup_middlewares
from app.routes import rss, user
from app.services.database import init_db

# 可以使用 zero code 的形式, 但不能使用 --reload 参数启动 fastapi 服务
# from app.tracer import initialize_tracer
# initialize_tracer()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


# sentry_sdk.init(
#     dsn="https://e9f71432bc7dff920e04da84e6b6fb85@o4509330816958464.ingest.us.sentry.io/4509330819907584",
#     integrations=[
#         LoggingIntegration(
#             level=logging.INFO,  # 记录 info 及以上级别的日志
#             event_level=logging.ERROR,  # 错误级别的日志上报到 Sentry
#         )
#     ],
#     send_default_pii=True,
# )

app = FastAPI(lifespan=lifespan)


app.include_router(user.router)
app.include_router(rss.router)

setup_extentions(app)
setup_exception_handlers(app)
setup_middlewares(app)


@app.get("/whoami")
async def root():
    return {"whoami": "api.rss.navydev.top"}


@app.get("/sentry-debug")
async def trigger_error():
    _ = 1 / 0
