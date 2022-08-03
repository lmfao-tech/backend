import random
from typing import Optional
from os import environ as env

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from rich import print
from dotenv import load_dotenv
from pytwitter import StreamApi
from pytwitter import Api
from rich.traceback import install
from datetime import datetime, timedelta

from helpers import reset_rules, shuffle_list, repeat_every
from _types import Tweet
from server import Server

load_dotenv()

from redis_helpers import Blocked, Meme, MemeCache, get_blocked, get_cache

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

cache: MemeCache = get_cache()  # type: ignore
blocked: Blocked = get_blocked()  # type: ignore


def filter_tweet(tweet: Tweet) -> Optional[Meme]:

    if not "includes" in tweet:
        return
    created_at = datetime.strptime(
        tweet["includes"]["users"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
    )

    if created_at > datetime.now() - timedelta(days=10):
        print("[red]User acc created less than 10 days ago, skipping[/red]")
        return
    if not "media" in tweet["includes"]:
        print("[red]No media, skipping[/red]")
        return
    if not tweet["includes"]["media"][0]["type"] == "photo":
        print("[red]Not a photo, skipping[/red]")
        return
    if tweet["data"]["text"].startswith("RT "):
        print("[red]Is a retweet, skipping[/red]")
        return

    if any(keyword in tweet["data"]["text"].lower() for keyword in blocked.keywords):
        print("[red]Is an ad, skipping[/red]")
        return

    if tweet["includes"]["users"][0]["username"].lower() in " ".join(blocked.users):  # type: ignore
        print("[red]Is a blocked user, skipping[/red]")
        return

    if "urls" in tweet["data"]["entities"]:
        if any(
            url in tweet["data"]["entities"]["urls"][0]["expanded_url"]
            for url in blocked.urls  # type: ignore
        ):
            print("[red]Is a blocked url, skipping[/red]")
            return

    meme = Meme(
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
    if len(cache.memes) >= 300:
        cache.memes.pop(-1)

    stored_object = filter_tweet(tweet)

    if stored_object is None:
        return

    cache.memes.insert(0, stored_object)


stream.on_tweet = handle_tweet

if not dev:
    print(stream.get_rules())

# * AUTH AND TASKS


@app.on_event("startup")
@repeat_every(seconds=60 * 30)
def update_top_memes():
    """
    Update the top memes every 30 minutes
    """

    results = api.search_tweets(
        "(from:weirdrealitymp4 OR from:IntrovertProbss OR from:OldMemeArchive OR from:ManMilk2 OR from:dankmemesreddit OR from:SpongeBobMemesZ OR from:WholesomeMeme OR from:memes OR from:memeadikt) has:images -is:retweet lang:en -is:reply",
        tweet_fields=["created_at"],
        user_fields=[
            "username",
            "name",
            "profile_image_url",
            "created_at",
        ],  # To get the username
        expansions=["attachments.media_keys", "author_id"],
        media_fields=["preview_image_url", "url"],  # To get the image
        return_json=True,  # Return JSON because pytwitter doesn't return the `includes` key
        max_results=100,
    )
    assert isinstance(results, dict)
    for tweet in results["data"]:
        user_id = tweet["author_id"]
        media_id = tweet["attachments"]["media_keys"][0]

        user = next(
            (user for user in results["includes"]["users"] if user["id"] == user_id),
            None,
        )

        attachment = next(
            (
                attachment
                for attachment in results["includes"]["media"]
                if attachment["media_key"] == media_id
            ),
            None,
        )

        if not user or not attachment:
            continue

        new_object = Meme(
            username=user["username"],
            user=user["name"],
            profile_image_url=user["profile_image_url"],
            user_id=user["id"],
            tweet_id=tweet["id"],
            tweet_text=tweet["text"],
            tweet_link=f"https://twitter.com/{user['username']}/status/{tweet['id']}",
            tweet_created_at=datetime.strptime(
                tweet["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
            ),
            meme_link=attachment["url"],
            source="Top Creators",
        )

        cache.top_memes.insert(0, new_object)

        cache.top_memes = cache.top_memes[:300]

    cache.save()


@app.on_event("startup")
@repeat_every(seconds=60 * 3)
def save_cache():
    """Saves the current cache to the server every 3 minutes"""
    print("[blue]Saving Cache[/blue]")
    cache.save()
    print(f"{len(cache.memes)} memes, {len(cache.top_memes)} top memes saved.")
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


@app.get("/get_memes")
async def get_memes(last_id: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""

    if last_id == 0:
        return cache.memes[:max_tweets]

    top_n = max_tweets // 4

    # Get the meme with the last_id
    for meme in cache.memes:
        if meme.tweet_id == str(last_id):
            memes = cache.memes[
                cache.memes.index(meme)
                + 1 : cache.memes.index(meme)
                + 1
                + max_tweets
                - top_n
            ]

            top_index = random.Random(last_id).randint(0, len(cache.top_memes) - top_n)
            top_memes = cache.top_memes[top_index : top_index + top_n]

            return shuffle_list(memes + top_memes)

    return cache.memes[:max_tweets]


@app.get("/community_memes")
async def community_memes(last_id: int = 0, max_tweets: int = 20):

    if last_id == 0:
        return cache.community_memes[:max_tweets]

    # Get the meme with the last_id
    for meme in cache.community_memes:
        if meme.tweet_id == str(last_id):
            return cache.community_memes[
                cache.community_memes.index(meme)
                + 1 : cache.community_memes.index(meme)
                + 1
                + max_tweets
            ]

    return cache.community_memes[:max_tweets]


# * MODERATION ENDPOINTS
# TODO: Redis cache for the moderation endpoints
# @app.get("/revive_meme")
# async def revive_post(id: str):

#     global new_memes, top_memes_, community_memes_, removed_memes_list

#     for i, d in enumerate(removed_memes_list):
#         if d["tweet_id"] == id:
#             removed_memes_list.pop(i)
#             new_memes.append(d)

#     return {"message": "done"}


# @app.get("/removed_memes")
# async def removed_memes(last: int = 0, max_tweets: int = 20):
#     """Get the removed memes stored in cache"""
#     global removed_memes_list

#     return removed_memes_list[last : last + max_tweets]


# @app.get("/remove_meme")
# async def remove_a_post(id: str, by: str):

#     global new_memes, top_memes_, community_memes_, removed_memes_list
#     da_meme = None

#     for i, d in enumerate(new_memes):
#         if d["tweet_id"] == id:
#             da_meme = d
#             new_memes.pop(i)
#     for i, d in enumerate(top_memes_):
#         if d["tweet_id"] == id:
#             da_meme = d
#             top_memes.pop(i)
#     for i, d in enumerate(community_memes_):
#         if d["tweet_id"] == id:
#             da_meme = d
#             community_memes_.pop(i)

#     already_exists = False
#     for e in removed_memes_list:
#         if e["tweet_id"] == id:
#             already_exists = True

#     if not already_exists and da_meme:
#         da_meme["removed_by"] = by
#         removed_memes_list.append(da_meme)

#     return {"message": "done"}

config = uvicorn.Config(app=app, host="0.0.0.0")
if dev:
    print("[green]Running in development mode[/green]")
    config = uvicorn.Config(app="main:app", reload=True, debug=True)
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
