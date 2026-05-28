from fastapi import HTTPException, Request, status

from settings import ALLOWED_IPS


def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    x_real_ip = request.headers.get("X-Real-IP")
    return x_real_ip if x_real_ip else request.client.host


async def ip_filter(request: Request, call_next):
    """IP 白名单过滤；ALLOWED_IPS 含 * 时放行所有 IP。"""
    if "*" in ALLOWED_IPS:
        return await call_next(request)

    client_ip = get_client_ip(request)

    if client_ip not in ALLOWED_IPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied for IP: {client_ip}",
        )

    return await call_next(request)
