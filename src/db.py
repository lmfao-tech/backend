import redis
from os import environ as env

def connect_to_redis():
    r = redis.Redis(
        host=env.get("REDIS_URL"),  # type: ignore
        port=37425,
        password=env.get("REDIS_PASSWORD"),
        ssl=True,
    )
    try:
        r.ping()
    except redis.exceptions.ConnectionError:
        print("[redis] Connection error")
        exit(1)
    
    return r