from optparse import Option
import random
from typing import Dict, List, Literal, Optional, TypedDict
from os import environ as env

import uvicorn
from rich import print
from pytwitter import Api
from functools import lru_cache
from dotenv import load_dotenv
from pytwitter import StreamApi
from rich.traceback import install
from fastapi import FastAPI, Request
from datetime import datetime, timedelta
from fastapi.responses import RedirectResponse

from _types import Tweet
from server import Server
from helpers import lru_cache_with_ttl, reset_rules, shuffle_list, repeat_every

load_dotenv()

from redis_om import Migrator
from redis_helpers import redis, Blocked, Meme, get_blocked

install()
app = FastAPI()
dev = (
    env.get("ENV") == "development"
)  #! Development environment turns off authorization for quick testing
is_rule_ok = True  # If set to false, it will delete all the rules and use the RULES from src\data.py
stream = StreamApi(bearer_token=env.get("TWITTER_BEARER_TOKEN"))

if not is_rule_ok or not dev:
    reset_rules(stream)

api = Api(bearer_token=env.get("TWITTER_BEARER_TOKEN"))

blocked: Blocked = get_blocked()  # type:ignore

mods: Dict[str, int] = {}


def filter_tweet(tweet: Tweet) -> Optional[Meme]:

    if not "includes" in tweet:
        return
    created_at = datetime.strptime(
        tweet["includes"]["users"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
    )

    if created_at > datetime.now() - timedelta(days=10):
        if dev:
            print("[red]User acc created less than 10 days ago, skipping[/red]")
        return
    if not "media" in tweet["includes"]:
        if dev:
            print("[red]No media, skipping[/red]")
        return
    if not tweet["includes"]["media"][0]["type"] == "photo":
        if dev:
            print("[red]Not a photo, skipping[/red]")
        return
    if tweet["data"]["text"].startswith("RT "):
        if dev:
            print("[red]Is a retweet, skipping[/red]")
        return

    if any(keyword in tweet["data"]["text"].lower() for keyword in blocked.keywords):
        if dev:
            print("[red]Is an ad, skipping[/red]")
        return

    if tweet["includes"]["users"][0]["username"].lower() in " ".join(blocked.users):  # type: ignore
        if dev:
            print("[red]Is a blocked user, skipping[/red]")
        return

    if "urls" in tweet["data"]["entities"]:
        if any(
            url in tweet["data"]["entities"]["urls"][0]["expanded_url"]
            for url in blocked.urls  # type: ignore
        ):
            if dev:
                print("[red]Is a blocked url, skipping[/red]")
            return

    meme = Meme(
        page="main",
        username=tweet["includes"]["users"][0]["username"],
        user=tweet["includes"]["users"][0]["name"],
        profile_image_url=tweet["includes"]["users"][0]["profile_image_url"],
        user_id=tweet["includes"]["users"][0]["id"],
        tweet_id=tweet["data"]["id"],
        tweet_text=tweet["data"]["text"],
        tweet_link=f"https://twitter.com/{tweet['includes']['users'][0]['username']}/status/{tweet['data']['id']}",
        tweet_created_at=created_at,
        meme_link=tweet["includes"]["media"][0]["url"],
        source="Recently uploaded",
    )

    return meme


def handle_tweet(tweet: Tweet):

    stored_object = filter_tweet(tweet)

    if stored_object is None:
        return

    stored_object.expire(num_seconds=60 * 60 * 2)
    stored_object.save()


stream.on_tweet = handle_tweet
stream.on_request_error = lambda resp: print(f"[red]{resp}[/red]")
stream.on_closed = lambda resp: print("[red]Stream closed[/red]" + resp)

if not dev:
    print(stream.get_rules())

# * AUTH AND TASKS


@app.on_event("startup")
@repeat_every(seconds=60 * 30)
def do_tasks():
    """
    Update the moderators list every 30 minutes
    """
    blocked.save()

    removed_memes: List[Meme] = Meme.find(
        Meme.removed_by != None,
    ).all()  # type: ignore

    print(removed_memes)
    for meme in removed_memes:
        if not meme.removed_by:
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
    print(len(memes))
    latest: List[Meme] = []
    if len(memes) > TOTAL:
        to_be_removed = len(memes) - TOTAL

        for i in range(len(memes)):
            if i < to_be_removed:
                memes[i].delete(pk=memes[i].pk)
    # TODO
    #         else:
    #             print(i)
    #             if memes[i].removed_by == None:
    #                 latest.append(memes[i])

    # for i, meme in enumerate(latest):
    #     meme.update(index=i)

    blocked.save()


@app.get("/hello")
def hello():
    return {"message": "Hello World!"}


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


@lru_cache_with_ttl(ttl=90)
def get_all_memes(page):
    # , last=0, max_tweets=20

    memes = Meme.find(
        (
            Meme.page == page
        )  # & (Meme.index >= last) & (Meme.index <= last + max_tweets)
    ).all()

    return memes


@app.get("/get_memes")
async def get_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    all_memes = get_all_memes("main")  # last, max_tweets

    return {
        "memes": all_memes[last : last + max_tweets],
        "meta": {"total": len(all_memes), "sent": max_tweets, "last": last + max_tweets},
    }


@app.get("/community_memes")
async def community_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    community_memes_ = get_all_memes("community")  # , last, max_tweets

    return {"memes": community_memes_[last : last + max_tweets]}


@app.get("/profile_memes")
async def profile(username: str, last: int = 0, max_tweets: int = 20):
    """Get the profile of a user"""
    memes = Meme.find(Meme.username == username).all()

    return {"memes": memes[last : last + max_tweets], "meta": {"total": len(memes)}}


@app.get("/get_meme")
async def get_meme(tweet_id: int):
    """Get a specific meme"""

    meme = Meme.find(Meme.tweet_id == str(tweet_id)).first()

    if meme is None:
        return {"message": "Meme not found"}

    return meme


# * MODERATION ENDPOINTS
# TODO: Redis cache for the moderation endpoints
@app.get("/revive_meme")
async def revive_post(id: str):

    meme: Meme = Meme.find(Meme.tweet_id == id).first()  # type:ignore
    meme.update(removed_by=None)

    return {"message": "done"}


@app.get("/removed_memes")
async def removed_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    removed_memes_ = Meme.find(Meme.removed_by != None).all()
    print(removed_memes_)
    if last == 0:
        return {"memes": removed_memes_[:max_tweets]}
    else:
        return {"memes": removed_memes_[last : last + max_tweets]}


@app.get("/remove_meme")
async def remove_a_post(id: str, by: str):

    for meme in Meme.find(Meme.tweet_id == id).all():
        if meme.removed_by is None:  # type: ignore
            meme.update(removed_by=by)
            meme.expire(num_seconds=60 * 60 * 2)
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
        "cached": str(
            len(Meme.find((Meme.page == "main") & (Meme.removed_by == None)).all())
        ),
        # "removed": str(len(Meme.find(Meme.removed_by != None).all())),
        "community": str(len(Meme.find(Meme.page == "community").all())),
    }
    print(total)

    return {
        "blocked": blocked.users,
        "urls": blocked.urls,
        "keywords": blocked.keywords,
        "total": {},
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
    config = uvicorn.Config(app=app, reload=True, debug=True)
server = Server(config)


with server.run_in_thread():
    stream.search_stream(
        tweet_fields=["created_at", "entities"],
        user_fields=[
            "username",
            "name",
            "profile_image_url",
            "created_at",
        ],  # To get the username
        expansions=["attachments.media_keys", "author_id"],
        media_fields=["preview_image_url", "url"],  # To get the image
        return_json=True,  # Return JSON because pytwitter doesn't return the `includes` key
    )
