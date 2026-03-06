import redis
from decouple import config

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(config("REDIS_URL"), decode_responses=True)
    return _redis_client


def set_user_online(user_id: int):
    r = get_redis()
    r.setex(f"online:{user_id}", 35, "1")


def set_user_offline(user_id: int):
    r = get_redis()
    r.delete(f"online:{user_id}")


def is_user_online(user_id: int) -> bool:
    r = get_redis()
    return r.exists(f"online:{user_id}") == 1


def get_online_user_ids() -> list:
    r = get_redis()
    keys = r.keys("online:*")
    return [int(k.split(":")[1]) for k in keys]