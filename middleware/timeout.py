import asyncio

from fastapi import Request

from settings import SVR_TIMEOUT


async def timeout_handler(request: Request, call_next):
    return await asyncio.wait_for(call_next(request), SVR_TIMEOUT or 10)
