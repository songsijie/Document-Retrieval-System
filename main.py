import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

from app.retrieval.router import router as retrieval_router
from app.test.router import router as test_router
from base.es import get_es_client
from base.es_index import ensure_es_index
from middleware.exception import exception_handler
from middleware.ip_filter import ip_filter
from middleware.log import log_handler
from middleware.rate_limit import rate_limit
from middleware.response import response_handler
from middleware.timeout import timeout_handler
from settings import APP_NAME, ES_INDEX, IS_DEBUG, MIDDLEWARE_EXCLUDE_PATHS

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务启动时检查并创建 ES 索引。"""
    try:
        created = ensure_es_index(get_es_client())
        if created:
            logger.info("Created Elasticsearch index: %s", ES_INDEX)
    except Exception as exc:
        logger.warning("Failed to ensure Elasticsearch index: %s", exc)
    yield


app = FastAPI(
    title=APP_NAME,
    docs_url="/docs" if IS_DEBUG else None,
    redoc_url="/redoc" if IS_DEBUG else None,
    openapi_url="/openapi.json" if IS_DEBUG else None,
    lifespan=lifespan,
)

# 注册文献检索相关接口，统一挂载在 /retrieval 前缀下。
app.include_router(retrieval_router, prefix="/retrieval")
app.include_router(test_router, prefix="/test")

# 挂载基础中间件：响应包装、限流、IP 过滤、超时、日志和统一异常处理。
app.middleware("http")(response_handler)
app.middleware("http")(rate_limit)
app.middleware("http")(ip_filter)
app.middleware("http")(timeout_handler)
app.middleware("http")(log_handler)
app.middleware("http")(exception_handler)

# 自定义 OpenAPI 文档：非排除路径的响应展示统一包装格式。
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=APP_NAME,
        version="1.0.0",
        description=APP_NAME,
        routes=app.routes,
    )

    for path_key, path in openapi_schema["paths"].items():
        if path_key in MIDDLEWARE_EXCLUDE_PATHS:
            continue
        for method in path.values():
            if "responses" not in method:
                continue
            for response in method["responses"].values():
                original_schema = response.get("content", {}).get("application/json", {}).get("schema", {})
                response["content"] = {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "integer", "example": 0},
                                "message": {"type": "string", "example": "ok"},
                                "data": original_schema,
                            },
                        }
                    }
                }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


class HealthResponse(BaseModel):
    status: str = Field(..., description="服务状态")
    timestamp: str = Field(..., description="当前时间，ISO 格式")


# 最小健康检查接口，不依赖 ES 或其他外部服务。
@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now().isoformat())
