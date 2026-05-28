import asyncio
import datetime
import inspect
import json
from collections.abc import Awaitable, Callable
from decimal import Decimal
from functools import wraps
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel
from redis import asyncio as aredis

from base.cache import RedisLock, make_key


def _default_serialize(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, datetime.datetime):
        return obj.isoformat(timespec="seconds")
    raise TypeError(f"Type {type(obj)} not serializable")


def serialize(data: Any) -> str:
    return json.dumps(data, default=_default_serialize, ensure_ascii=False)


def deserialize(data: str) -> Any:
    return json.loads(data)


# 解析异步参数
async def _resolve(arg):
    return await arg if inspect.isawaitable(arg) else arg


def cache_key_fn(key: str) -> str:
    return make_key(f"cache:{key}")


def cache_fn(
    redis_client: aredis.Redis,
    get_key: Callable[..., str],
    expire: int,
    wait: int = 5,
    nowait: bool = False,
):
    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            use_cache = kwargs.pop("use_cache", True)
            if not use_cache:
                return await fn(*args, **kwargs)
            else:
                args_values = await asyncio.gather(*[_resolve(arg) for arg in args])
                kwargs_values = {k: await _resolve(v) for k, v in kwargs.items()}
                key = get_key(*args_values, **kwargs_values)
                cache_key = cache_key_fn(key)
                cached_result = await redis_client.get(cache_key)
                if cached_result:
                    return deserialize(cached_result)

                async with RedisLock(
                    redis_client=redis_client,
                    lock_key=lock_key_fn(key),
                    lock_timeout=expire,
                    acquire_timeout=wait,
                    nowait=nowait,
                ):
                    result = await fn(*args_values, **kwargs_values)
                json_str_result = serialize(result)
                await redis_client.set(cache_key, json_str_result, ex=expire)
                return deserialize(json_str_result)

        return wrapper

    return decorator


def lock_key_fn(key: str) -> str:
    return make_key(f"lock:{key}")


def lock_fn(
    redis_client: aredis.Redis,
    get_key: Callable[..., str],
    expire: int = 10,
    wait: int = 5,
    nowait: bool = False,
):
    def decorator(fn: Callable[..., Awaitable[Any]]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            args_values = await asyncio.gather(*[_resolve(arg) for arg in args])
            kwargs_values = {k: await _resolve(v) for k, v in kwargs.items()}
            key = lock_key_fn(get_key(*args_values, **kwargs_values))

            async with RedisLock(
                redis_client=redis_client,
                lock_key=key,
                lock_timeout=expire,
                acquire_timeout=wait,
                nowait=nowait,
            ):
                return await fn(*args, **kwargs)

        return wrapper

    return decorator


async def clean_cache(
    redis_client: aredis.Redis,
    *cache_keys: str,
):
    await redis_client.delete(*(cache_key_fn(k) for k in cache_keys))


incr_expire_script = """
local current
current = redis.call("INCR", KEYS[1])
if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return current
"""


def rate_limit(
    redis_client: aredis.Redis,
    get_key: Callable[..., str],
    max_reqs: int,
    time_window: int,
):
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 根据模式确定标识符
            args_values = await asyncio.gather(*[_resolve(arg) for arg in args])
            kwargs_values = {k: await _resolve(v) for k, v in kwargs.items()}
            key = f"rate_limit:{get_key(*args_values, **kwargs_values)}"

            current_reqs = await redis_client.eval(incr_expire_script, 1, key, time_window)
            if int(current_reqs) > max_reqs:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def retry(max_attempts: int, delay: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
