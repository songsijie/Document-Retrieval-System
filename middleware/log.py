import json
import logging

from fastapi import Request

from settings import MIDDLEWARE_EXCLUDE_PATHS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")


async def log_handler(request: Request, call_next):
    # 直接跳过无需记录的路径
    if any(path in request.url.path for path in MIDDLEWARE_EXCLUDE_PATHS):
        return await call_next(request)

    # start_time = time.perf_counter()

    # 记录请求基本信息
    request_info = {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
    }

    if "application/json" in request.headers.get("content-type", ""):
        body_bytes = await request.body()
        try:
            request_info["body"] = json.loads(body_bytes.decode()) if body_bytes else None
        except Exception:
            request_info["body"] = "<cannot parse json>"

    # 执行下个中间件
    response = await call_next(request)

    # 计算总耗时（毫秒） 写入响应头
    # response.headers["X-Process-Time"] = f"{int((time.perf_counter() - start_time) * 1000)}ms"

    # 记录响应基本信息
    response_body = getattr(request.state, "response_body", None)
    response_info = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response_body,
    }

    io_data = {
        "request": request_info,
        "response": response_info,
    }

    if response.status_code >= 400 or (response_body and response_body.get("code", 0) != 0):
        logger.error(json.dumps(io_data, ensure_ascii=False))
    else:
        logger.info(json.dumps(io_data, ensure_ascii=False))
    return response
