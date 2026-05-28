from fastapi import HTTPException, Request, status

from settings import RATE_LIMIT_EXCLUDE_PATHS

# 时间窗口
time_window = 60
# 最大请求数
max_reqs = 200


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    x_real_ip = request.headers.get("X-Real-IP")
    return x_real_ip if x_real_ip else request.client.host


async def rate_limit(request: Request, call_next):
    """限流中间件"""
    # 获取客户端 IP 地址
    client_ip = get_client_ip(request)

    # 获取请求路径
    if request.url.path not in RATE_LIMIT_EXCLUDE_PATHS:
        from base.cache import redis_client
        from base.decorator import incr_expire_script

        key = f"rate_limit:ip:{client_ip}"

        current_reqs = await redis_client.eval(incr_expire_script, 1, key, time_window)
        if int(current_reqs) > max_reqs:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
            )

    return await call_next(request)
