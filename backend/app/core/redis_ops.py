# Redis 限流与分布式锁



import secrets

from app.core.redis import redis_client

_LUA_RELEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""

# 基于Redis的限流器
async def hit_rate_limit(bucket: str, limit: int, window_seconds: int) -> bool:
    key = f"rl:{bucket}"                                         # 生成唯一计数器key,
    count = await redis_client.incr(key)                         # 计数器自增
    if count == 1:                                               
        await redis_client.expire(key, window_seconds)           # 第一次访问，设置过期时间
    elif count > limit and await redis_client.ttl(key) < 0:      # 如果计数已经超限，但是TTL丢失了，重新设置过期时间
        await redis_client.expire(key, window_seconds)
    return count > limit                                         # 如果计数超过限制，返回 True（被限流）


"""
在多个服务器节点同时竞争同一个资源时，保证只有一个节点抢到锁

nx = true保证了只有第一个到达的请求能写入成功，后续请求全部失败
token表示生成不可伪造的身份凭证，
lock:{name} 表示锁的key，用于存储锁的状态
ex=ttl_seconds 表示锁的过期时间，防止异常导致永久占用锁


ok这一行表示上锁成功，返回token，后续请求需要携带token才能解锁，并设置超时自动开门

"""

async def try_lock(name: str, ttl_seconds: int) -> str | None:
    token = secrets.token_urlsafe(16)
    ok = await redis_client.set(f"lock:{name}", token, nx=True, ex=ttl_seconds)
    return token if ok else None




# return True：令牌匹配解锁成功
# return False：令牌不匹配解锁失败
async def release_lock(name: str, token: str) -> bool:
    return bool(await redis_client.eval(_LUA_RELEASE, 1, f"lock:{name}", token))


async def renew_lock(name: str, token: str, ttl_seconds: int) -> bool:
    return bool(await redis_client.eval(
        "if redis.call('get', KEYS[1]) == ARGV[1] then "
        "return redis.call('expire', KEYS[1], ARGV[2]) else return 0 end",
        1, f"lock:{name}", token, ttl_seconds,
    ))
