from typing import Dict, List, Literal, Optional, TypedDict
from os import environ as env

import uvicorn
from rich import print
from pytwitter import Api
from dotenv import load_dotenv
from rich.traceback import install
from fastapi import FastAPI, Request
from datetime import datetime, timedelta
from fastapi.responses import RedirectResponse

from _types import Tweet
from server import Server
from helpers import lru_cache_with_ttl, reset_rules, repeat_every

load_dotenv()

from redis_om import Migrator
from redis_helpers import redis, Blocked, Meme, get_blocked
from honeybadger import honeybadger
honeybadger.configure(api_key=env.get("HONEYBADGER_API_KEY"))

install()
app = FastAPI()
dev = (
    env.get("ENV") == "development"
)  #! Development environment turns off authorization for quick testing
is_rule_ok = True  # If set to false, it will delete all the rules and use the RULES from src\data.py

blocked: Blocked = get_blocked()  # type:ignore

mods: Dict[str, int] = {}


@lru_cache_with_ttl(ttl=120)
def get_removed_memes():
    removed_memes: List[Meme] = Meme.find().all()  # type: ignore
    r = []
    for meme in removed_memes:
        if not meme.removed_by == "":
            r.append(meme)
    r.reverse()
    return r


@lru_cache_with_ttl(ttl=90)
def get_all_memes(page) -> List[Meme]:
    memes: List[Meme] = Meme.find((Meme.page == page)).all()  # type: ignore
    return memes


@lru_cache_with_ttl(ttl=90)
def get_profile(username: str):
    memes = Meme.find(Meme.username == username).all()
    memes.reverse()
    return memes


@lru_cache_with_ttl(ttl=60)
def get_tweet(tweet_id):
    meme = Meme.find(Meme.tweet_id == str(tweet_id)).first()
    return meme


@app.on_event("startup")
@repeat_every(seconds=60 * 30)
def do_tasks():
    """
    Update the moderators list every 30 minutes
    """
    print("Doing 30m tasks")
    blocked.save()

    removed_memes = get_removed_memes()

    for meme in removed_memes:
        if meme.removed_by == "" or not meme.removed_by:
            continue
        if meme.removed_by in mods.keys():
            mods[meme.removed_by] += 1
        else:
            mods[meme.removed_by] = 1


@app.on_event("startup")
@repeat_every(seconds=60 * 2)
def save_cache():
    """Saves the current cache to the server every 2 minutes"""
    print("Saving cache and updating indexes")
    TOTAL = 200
    # Make sure memes "main" are not more than 200
    memes: List[Meme] = Meme.find(Meme.page == "main").all()  # type: ignore

    if len(memes) > TOTAL:
        to_be_removed = len(memes) - TOTAL

        for i in range(len(memes)):
            if i < to_be_removed:
                memes[i].delete(pk=memes[i].pk)

    blocked.save()

@app.get("/unauthorized", status_code=401)
def unauthorized():
    # return 401 status
    return {"message": "Unauthorized"}

# Middleware for authorization
if not dev:

    @app.middleware("http")
    async def authenticate(request: Request, call_next):

        if request.url.path == "/unauthorized":
            # Don't do anything for this route
            return await call_next(request)

        if request.headers.get("Authorization") == env.get("AUTH_PASSWORD"):
            return await call_next(request)
        else:
            # Redirect to unauthorized page
            return RedirectResponse("/unauthorized")


# * GET ENDPOINTS


@app.get("/get_memes")
async def get_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    all_memes: List[Meme] = get_all_memes("main")  # last, max_tweets

    all_memes = [meme for meme in all_memes if meme.removed_by is not None]

    return {
        "memes": all_memes[last : last + max_tweets],
        "meta": {
            "total": len(all_memes),
            "sent": max_tweets,
            "last": last + max_tweets,
        },
    }


@app.get("/community_memes")
async def community_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    community_memes_ = get_all_memes("community")  # , last, max_tweets
    community_memes_.reverse()

    return {"memes": community_memes_[last : last + max_tweets]}


@app.get("/profile_memes")
async def profile(username: str, last: int = 0, max_tweets: int = 20):
    """Get the profile of a user"""
    memes = get_profile(username)
    return {"memes": memes[last : last + max_tweets], "meta": {"total": len(memes)}}


@app.get("/get_meme")
async def get_meme(tweet_id: int):
    """Get a specific meme"""
    meme = get_tweet(tweet_id)
    if meme is None:
        return {"message": "Meme not found"}

    return meme


# * MODERATION ENDPOINTS
@app.get("/revive_meme")
async def revive_post(id: str):

    meme: Meme = get_tweet(id)  # type: ignore
    meme.update(removed_by=None)

    return {"message": "done"}


@app.get("/removed_memes")
async def removed_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    removed_memes_ = get_removed_memes()

    if last == 0:
        return {"memes": removed_memes_[:max_tweets]}
    else:
        return {"memes": removed_memes_[last : last + max_tweets]}


@app.get("/remove_meme")
async def remove_a_post(id: str, by: str):
    memes: List[Meme] = Meme.find(Meme.tweet_id == id).all()  # type: ignore
    memes[0].update(removed_by=by)
    memes[0].expire(num_seconds=24 * 60 * 60)
    memes[0].save()
    return {"message": "done"}


@app.get("/ban_user")
async def ban_user(user: str):
    """Ban a user from the automated stream"""
    blocked.users.append(user)
    blocked.save()

    Meme.find(Meme.username == user).delete()

    return {"message": "done"}


@app.get("/unban_user")
async def unban_user(user: str):
    """Unban a user from the automated stream"""
    blocked.users.remove(user)
    blocked.save()

    return {"message": "done"}


@app.get("/supermod")
async def supermod(
    word: Optional[str] = None,
    url: Optional[str] = None,
    users: Optional[str] = None,
    action: Literal["add", "remove"] = "add",
    password: str = "",
):
    """Supermod endpoint. Returns all blocked users, URLS, keywords. Number of posts removed by mods, number of cached,removed, community memes"""

    if password != env.get("SUPERMOD_PASSWORD"):
        return {"message": "Invalid password"}

    if action == "add":
        print("Adding word")
        if (word) and not word == "undefined":
            blocked.keywords.append(word)
        if url and not url == "undefined":
            blocked.urls.append(url)
        if users and not users == "undefined":
            blocked.users.append(users)
        blocked.save()

    elif action == "remove":
        if word and not word == "undefined":
            blocked.keywords.remove(word)
        if url and not url == "undefined":
            blocked.urls.remove(url)
        if users and not users == "undefined":
            blocked.users.remove(users)
        blocked.save()

    total = {
        "cached": str(len(get_all_memes("main"))),
        "removed": str(len(get_removed_memes())),
        "community": str(len(get_all_memes("community"))),
    }

    return {
        "blocked": blocked.users,
        "urls": blocked.urls,
        "keywords": blocked.keywords,
        "total": total,
        "mods": mods,
    }


# * UPLOAD ENDPOINTS
@app.post("/upload_meme")
async def upload_meme(data: Meme):
    """Upload a meme to the server"""
    print(f"[blue]Uploading meme: {data.tweet_text}[/blue]")
    data.save()
    return {"message": "done"}


config = uvicorn.Config(app=app, host="0.0.0.0")
if dev:
    print("[green]Running in development mode[/green]")
    config = uvicorn.Config(app=app, reload=True)
server = Server(config)

server.run()