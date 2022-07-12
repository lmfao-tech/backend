import random
import typing
from typing import List, Dict, Optional
from os import environ as env

import uvicorn
from fastapi import FastAPI
from rich import print
from dotenv import load_dotenv
from pytwitter import StreamApi
from pytwitter import Api
from rich.traceback import install
from datetime import datetime, timedelta

from helpers import is_valid_text, reset_rules, shuffle_list
from _types import Tweet, StoredObject, TweetSearchResult
from server import Server

load_dotenv()
install()

app = FastAPI()

# If set to false, it will delete all the rules and use the RULES from src\data.py
is_rule_ok = True

new_memes_dict: List[StoredObject] = []

stream = StreamApi(bearer_token=env.get("TWITTER_BEARER_TOKEN"))
api = Api(bearer_token=env.get("TWITTER_BEARER_TOKEN"))

def filter_tweet(tweet: Tweet) -> Optional[StoredObject]:
    if not "includes" in tweet:
        return
    created_at = datetime.strptime(
        tweet["includes"]["users"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
    )

    # If the created_at is less than one month ago, it will not be saved
    if created_at > datetime.now() - timedelta(days=30):
        print("[red]User acc created less than a month ago, skipping[/red]")
        return
    if not "media" in tweet["includes"]:
        print("[red]No media, skipping[/red]")
        return
    if not tweet["includes"]["media"][0]["type"] == "photo":
        print("[red]Not a photo, skipping[/red]")
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
    }

    return stored_object

def handle_tweet(tweet: Tweet):

    if len(new_memes_dict) >= 500:
        new_memes_dict.pop(0)

    stored_object = filter_tweet(tweet)

    if stored_object is None:
        return

    new_memes_dict.append(stored_object)


stream.on_tweet = handle_tweet

if not is_rule_ok:
    reset_rules(stream)


@app.get("/get_memes")
async def get_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    if last == 0:
        return shuffle_list(new_memes_dict[:max_tweets])
    else:
        # Find the index of the tweetId in the list
        return shuffle_list(new_memes_dict[last : last + max_tweets])



# Asynchrounosly start the server
config = uvicorn.Config(app=app, host="0.0.0.0")
server = Server(config)

with server.run_in_thread():
    print("[green]Starting stream[/green]")
    stream.search_stream(
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
    )
