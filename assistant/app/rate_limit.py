from fastapi import HTTPException, Request

from app.config import get_settings

_redis_client = None


def _redis():
    global _redis_client
    settings = get_settings()
    if not settings.redis_url:
        return None
    if _redis_client is None:
        import redis

        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def check_rate_limit(request: Request, bucket_suffix: str = "") -> None:
    settings = get_settings()
    client = _redis()
    if client is None:
        return

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    key = f"rl:chat:{ip}:{bucket_suffix}"
    count = client.incr(key)
    if count == 1:
        client.expire(key, 60)

    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Muitas mensagens. Aguarde um momento.")
