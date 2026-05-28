import json
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import settings


# 创建一个基础响应模型
class StandardResponse(BaseModel):
    code: int = Field(0, description="错误代码，0表示成功")
    message: str = Field("ok", description="响应消息或错误信息")
    data: dict | list[dict] | None = Field(None, description="响应数据")


# 统一修改所有响应
async def response_handler(request: Request, call_next):
    # 直接跳过无需处理的路径
    if any(path in request.url.path for path in settings.MIDDLEWARE_EXCLUDE_PATHS):
        return await call_next(request)

    start_time = time.perf_counter()

    response = await call_next(request)

    if "application/json" in response.headers.get("content-type", "") and 200 <= response.status_code < 300:
        # 读取并复制响应体
        response_body_bytes = b""
        async for chunk in response.body_iterator:
            response_body_bytes += chunk

        # 解析原始响应内容
        response_body = json.loads(response_body_bytes.decode()) if response_body_bytes else None

        # 构造统一响应体
        wrapped = StandardResponse(data=response_body)

        response = JSONResponse(status_code=response.status_code, content=wrapped.model_dump(exclude_none=True))

        # 存起来供其他中间件使用
        request.state.response_body = wrapped.model_dump(exclude_none=True)

    # 计算总耗时（毫秒） 写入响应头
    response.headers["X-Process-Time"] = f"{int((time.perf_counter() - start_time) * 1000)}ms"
    return response
