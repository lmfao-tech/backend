from typing import List, Optional
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

from helpers import reset_rules, shuffle_list
from _types import Tweet, StoredObject
from server import Server

load_dotenv()
install()

app = FastAPI()

# If set to false, it will delete all the rules and use the RULES from src\data.py
is_rule_ok = True

new_memes: List[StoredObject] = []
top_memes_: List[StoredObject] = []
top_memes_last_updated = datetime.utcnow()
community_memes_: List[StoredObject] = []
removed_memes_list: List[StoredObject] = []
community_memes_last_updated = datetime.utcnow()

api = Api(bearer_token=env.get("TWITTER_BEARER_TOKEN"))

BLOCKED_KEYWORDS = [
    "worth reading",
    "freecomic",
    "manhua",
    "love story",
    "BLcomics",
    "webtoon",
    "link",
]
BLOCKED_USERS = ["futurememesbot"]
BLOCKED_URLS = ["m.bilibilicomics", "bit.ly", "discord.gg"]


def filter_tweet(tweet: Tweet) -> Optional[StoredObject]:

    if not "includes" in tweet:
        return
    created_at = datetime.strptime(
        tweet["includes"]["users"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
    )

    # If the created_at is less than one month ago, it will not be saved
    if created_at > datetime.now() - timedelta(days=10):
        print("[red]User acc created less than 10 days ago, skipping[/red]")
        return
    if not "media" in tweet["includes"]:
        print("[red]No media, skipping[/red]")
        return
    if not tweet["includes"]["media"][0]["type"] == "photo":
        print("[red]Not a photo, skipping[/red]")
        return
    if "$" in tweet["data"]["text"]:
        print("[red]Contains a dollar sign, skipping[/red]")
        return
    if tweet["data"]["text"].startswith("RT "):
        print("[red]Is a retweet, skipping[/red]")
        return

    if any(keyword in tweet["data"]["text"].lower() for keyword in BLOCKED_KEYWORDS):
        print("[red]Is an ad, skipping[/red]")
        return

    if tweet["includes"]["users"][0]["username"].lower() in BLOCKED_USERS:
        print("[red]Is a blocked user, skipping[/red]")
        return

    if "urls" in tweet["data"]["entities"]:
        if any(
            url in tweet["data"]["entities"]["urls"][0]["expanded_url"]
            for url in BLOCKED_URLS
        ):
            print("[red]Is a blocked url, skipping[/red]")
            return

    stored_object: StoredObject = {
        "username": tweet["includes"]["users"][0]["username"],
        "user": tweet["includes"]["users"][0]["name"],
        "profile_image_url": tweet["includes"]["users"][0]["profile_image_url"],
        "tweet_id": tweet["data"]["id"],
        "user_id": tweet["includes"]["users"][0]["id"],
        "tweet_text": tweet["data"]["text"],
        "tweet_link": f"https://twitter.com/{tweet['includes']['users'][0]['username']}/status/{tweet['data']['id']}",
        "tweet_created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "meme_link": tweet["includes"]["media"][0]["url"],
        "source": "Recently uploaded"
    }

    return stored_object


stream = StreamApi(bearer_token=env.get("TWITTER_BEARER_TOKEN"))
if not is_rule_ok:
    reset_rules(stream)


def handle_tweet(tweet: Tweet):
    if len(new_memes) >= 500:
        new_memes.pop(0)

    stored_object = filter_tweet(tweet)

    if stored_object is None:
        return
    new_memes.append(stored_object)


stream.on_tweet = handle_tweet

print(stream.get_rules())


@app.get("/unauthorized", status_code=401)
def unauthorized():
    # return 401 status
    return {"message": "Unauthorized"}


# Middleware for authorization
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


@app.get("/get_memes")
async def get_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    global new_memes

    return shuffle_list(new_memes[last : last + max_tweets])


@app.get("/top_memes")
async def top_memes(last: int = 0, max_tweets: int = 20):
    """Get the top memes"""

    global top_memes_last_updated
    global top_memes_

    if top_memes_last_updated > datetime.utcnow() - timedelta(hours=1):
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
        if not isinstance(results, dict):
            return []
        for tweet in results["data"]:
            user_id = tweet["author_id"]
            media_id = tweet["attachments"]["media_keys"][0]

            user = next(
                (
                    user
                    for user in results["includes"]["users"]
                    if user["id"] == user_id
                ),
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

            new_obj: StoredObject = {
                "tweet_id": str(tweet["id"]),
                "tweet_text": tweet["text"],
                "user_id": str(tweet["author_id"]),
                "tweet_created_at": tweet["created_at"],
                "user": user["name"],
                "username": user["username"],
                "profile_image_url": user["profile_image_url"],
                "meme_link": attachment["url"],
                "tweet_link": f"https://twitter.com/{user['username']}/status/{tweet['id']}",
                "source": "popular",
            }

            top_memes_.append(new_obj)

        top_memes_last_updated = datetime.utcnow()

    return shuffle_list(top_memes_[last : last + max_tweets])


@app.get("/community_memes")
async def community_memes(last: int = 0, max_tweets: int = 20):
    global community_memes_
    global community_memes_last_updated

    if community_memes_last_updated > datetime.utcnow() - timedelta(minutes=15):
        results = api.search_tweets(
            "#LMFAOtech has:images -is:retweet lang:en -is:reply",
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
            start_time=datetime.strftime(
                datetime.utcnow() - timedelta(weeks=50), "%Y-%m-%d"
            ),
        )
        if not isinstance(results, dict):
            return []
        for tweet in results["data"]:
            user_id = tweet["author_id"]
            media_id = tweet["attachments"]["media_keys"][0]

            user = next(
                (
                    user
                    for user in results["includes"]["users"]
                    if user["id"] == user_id
                ),
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

            new_obj: StoredObject = {
                "tweet_id": str(tweet["id"]),
                "tweet_text": tweet["text"],
                "user_id": str(tweet["author_id"]),
                "tweet_created_at": tweet["created_at"],
                "user": user["name"],
                "username": user["username"],
                "profile_image_url": user["profile_image_url"],
                "meme_link": attachment["url"],
                "tweet_link": f"https://twitter.com/{user['username']}/status/{tweet['id']}",
                "source": "popular",
            }

            community_memes_.append(new_obj)

        community_memes_last_updated = datetime.utcnow()

    return shuffle_list(community_memes_[last : last + max_tweets])


#* MODERATION ENDPOINTS
@app.get("/revive_meme")
async def revive_post(id: str):

    global new_memes, top_memes_, community_memes_, removed_memes_list

    for i, d in enumerate(removed_memes_list):
        if d["tweet_id"] == id:
            removed_memes_list.pop(i)
            new_memes.append(d)

    return {"message": "done"}


@app.get("/removed_memes")
async def removed_memes(last: int = 0, max_tweets: int = 20):
    """Get the removed memes stored in cache"""
    global removed_memes_list

    return removed_memes_list[last : last + max_tweets]


@app.get("/remove_meme")
async def remove_a_post(id: str, by: str):

    global new_memes, top_memes_, community_memes_, removed_memes_list
    da_meme = None

    for i, d in enumerate(new_memes):
        if d["tweet_id"] == id:
            da_meme = d
            new_memes.pop(i)
    for i, d in enumerate(top_memes_):
        if d["tweet_id"] == id:
            da_meme = d
            top_memes.pop(i)
    for i, d in enumerate(community_memes_):
        if d["tweet_id"] == id:
            da_meme = d
            community_memes_.pop(i)

    already_exists = False
    for e in removed_memes_list:
        if e["tweet_id"] == id:
            already_exists = True

    if not already_exists and da_meme:
        da_meme["removed_by"] = by
        removed_memes_list.append(da_meme)

    return {"message": "done"}

config = uvicorn.Config(app=app, host="0.0.0.0")
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
