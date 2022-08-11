from datetime import datetime
from typing import List, Any, Callable, Optional, Awaitable
import asyncio
from functools import wraps
from starlette.concurrency import run_in_threadpool
import random
from pytwitter import StreamApi
from pytwitter.models import Response
from data import RULES
from emoji import EMOJI_DATA
from functools import lru_cache, wraps
from time import monotonic


def lru_cache_with_ttl(maxsize=128, typed=False, ttl=60):
    """Least-recently used cache with time-to-live (ttl) limit."""

    class Result:
        __slots__ = ('value', 'death')

        def __init__(self, value, death):
            self.value = value
            self.death = death

    def decorator(func):
        @lru_cache(maxsize=maxsize, typed=typed)
        def cached_func(*args, **kwargs):
            value = func(*args, **kwargs)
            death = monotonic() + ttl
            return Result(value, death)

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = cached_func(*args, **kwargs)
            if result.death < monotonic():
                result.value = func(*args, **kwargs)
                result.death = monotonic() + ttl
            return result.value

        wrapper.cache_clear = cached_func.cache_clear
        return wrapper

    return decorator

def repeat_every(*, seconds: float, wait_first: bool = False):
    def decorator(func: Callable[[], Optional[Awaitable[None]]]):
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def wrapped():
            async def loop():
                if wait_first:
                    await asyncio.sleep(seconds)
                while True:
                    try:
                        if is_coroutine:
                            await func()  # type: ignore
                        else:
                            await run_in_threadpool(func)
                    except Exception as e:
                        print(e)
                    await asyncio.sleep(seconds)

            asyncio.create_task(loop())

        return wrapped

    return decorator


def del_rules(*id: int) -> dict:
    """
    Generate a dict to delete rules
    """
    return {"delete": {"ids": [str(id) for id in id]}}


def del_all(stream: StreamApi):
    """
    Delete all rules from the stream
    """
    rules = stream.get_rules()
    if isinstance(rules, Response):
        to_be_deleted: List[int] = []
        if rules.data:
            to_be_deleted = [int(rule.id) for rule in rules.data]  # type: ignore

        if len(to_be_deleted) > 0:
            stream.manage_rules(del_rules(*to_be_deleted))

        return to_be_deleted


def reset_rules(stream: StreamApi):
    """
    Delete all rules and add the default ones
    """
    del_all(stream)
    stream.manage_rules(rules=RULES)
    print(stream.get_rules())


def is_valid_text(text: str):
    for char in text:
        if char and char.isdigit() and char not in EMOJI_DATA:
            return False
    return True


def shuffle_list(list_: List[Any], seed: Optional[int] = None):
    if not seed:
        seed = datetime.now().microsecond

    random.Random(seed).shuffle(list_)
    return list_


def reverse_list(list_: List[Any]):
    return list_[::-1]
