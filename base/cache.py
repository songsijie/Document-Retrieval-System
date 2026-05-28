import asyncio
import uuid

from redis import asyncio as aredis

from settings import CACHE_DB, CACHE_HOST, CACHE_KEYPREFIX, CACHE_PASSWORD, CACHE_PORT

redis_client = aredis.Redis(
    host=CACHE_HOST,
    port=CACHE_PORT,
    password=CACHE_PASSWORD,
    db=CACHE_DB,
    decode_responses=True,
)


def get_redis():
    return redis_client


def make_key(key: str):
    return f"{CACHE_KEYPREFIX}-{key}"


class RedisLock:
    def __init__(self, redis_client, lock_key, lock_timeout=10, acquire_timeout=10, nowait=False):
        self.redis_client = redis_client
        self.lock_key = lock_key
        self.lock_timeout = lock_timeout
        self.lock_value = str(uuid.uuid4())
        self.acquire_timeout = acquire_timeout
        self.nowait = nowait

    async def acquire(self):
        """尝试获取锁，带有超时设置。使用指数退避策略减少竞争冲突。"""
        end = asyncio.get_running_loop().time() + self.acquire_timeout
        delay = 0.1
        while asyncio.get_running_loop().time() < end:
            try:
                if await self.redis_client.set(self.lock_key, self.lock_value, ex=self.lock_timeout, nx=True):
                    return True
                if self.nowait:
                    return False
                await asyncio.sleep(delay)
                delay *= 2  # 指数退避
            except Exception as e:
                print(f"Error acquiring lock: {e}")
                await asyncio.sleep(delay)
        return False

    async def release(self):
        """释放锁。只有锁的持有者才能释放锁。"""
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            # 修复: 避免使用列表格式传递参数，直接传递参数
            result = await self.redis_client.eval(
                script,
                1,  # keys的数量
                self.lock_key,  # 第一个key
                self.lock_value,  # 第一个argv
            )
            print(f"Release lock result: {result}")
            return result != 0
        except Exception as e:
            print(f"Error releasing lock: {e}")
            return False

    async def extend(self, additional_time):
        """延长锁的时间。仅当锁仍有效时才能延长。"""
        try:
            ttl = await self.redis_client.ttl(self.lock_key)
            if ttl > 0:
                new_ttl = ttl + additional_time
                await self.redis_client.expire(self.lock_key, new_ttl)
                return True
        except Exception as e:
            print(f"Error extending lock: {e}")
        return False

    async def __aenter__(self):
        acquired = await self.acquire()
        if not acquired:
            raise RuntimeError("Lock could not be acquired")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
