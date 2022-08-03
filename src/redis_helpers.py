from typing import List, Optional
from datetime import datetime
from os import environ as env
from rich import print

from redis_om import (
    HashModel,
    get_redis_connection,
    EmbeddedJsonModel,
    Field,
    JsonModel,
)
from pydantic import AnyHttpUrl

redis = get_redis_connection(url=env.get("REDIS_OM_URL"))


class Meme(EmbeddedJsonModel):
    username: str
    user: str
    profile_image_url: AnyHttpUrl
    user_id: str
    tweet_id: str = Field(index=True)
    tweet_text: str
    tweet_link: AnyHttpUrl
    tweet_created_at: datetime
    meme_link: AnyHttpUrl
    source: str
    removed_by: Optional[str] = None

    class Meta:
        database = redis
        global_key_prefix = "meme:"


class MemeCache(JsonModel):
    memes: List[Meme] = []
    top_memes: List[Meme] = []
    community_memes: List[Meme] = []
    removed_memes: List[Meme] = []

    class Meta:
        database = redis
        global_key_prefix = "MemeCache:"


class Blocked(JsonModel):
    keywords: List[str] = []
    users: List[str] = []
    urls: List[str] = []

    class Meta:
        database = redis
        global_key_prefix = "blocked:"


def get_cache(cache_key: Optional[str] = None) -> JsonModel:

    for key in redis.scan_iter("MemeCache:*"):
        cache_key = key
        break

    if cache_key is None:
        memes = MemeCache()
        memes.save()
        cache_key = memes.pk

        print("[green]Created new server key[/green]")

    assert cache_key is not None

    if ":" in str(cache_key):
        cache_key = str(cache_key).split(":")[-1].strip("'")
    memes = MemeCache.get(pk=cache_key)

    return memes


def get_blocked(cache_key: Optional[str] = None) -> JsonModel:

    for key in redis.scan_iter("blocked:*"):
        cache_key = key
        break

    if cache_key is None:
        blocked = Blocked()
        blocked.save()
        cache_key = blocked.pk

        print("[green]Created new Blocked server key[/green]")

    assert cache_key is not None

    if ":" in str(cache_key):
        cache_key = str(cache_key).split(":")[-1].strip("'")
    print(cache_key)
    blocked = Blocked.get(pk=cache_key)

    return blocked
