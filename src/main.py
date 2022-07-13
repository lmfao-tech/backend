import random
import time
import typing
import logging
from typing import List, Dict, Optional, Tuple, Union
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

logging.basicConfig(filename="log.txt")

load_dotenv()
install()

app = FastAPI()

# If set to false, it will delete all the rules and use the RULES from src\data.py
is_rule_ok = False

new_memes: List[StoredObject] = []

api = Api(bearer_token=env.get("TWITTER_BEARER_TOKEN"))


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
        "source": "Recently uploaded",
    }

    return stored_object


class CustomStream(StreamApi):
    def __init__(self, bearer_token=None, consumer_key=None, consumer_secret=None, proxies=None, max_retries=3, timeout=None, chunk_size=1024):
        super().__init__(bearer_token, consumer_key, consumer_secret, proxies, max_retries, timeout, chunk_size)


    def handle_tweet(self,tweet: Tweet):
        if len(new_memes) >= 500:
            new_memes.pop(0)

        stored_object = filter_tweet(tweet)

        if stored_object is None:
            return
        new_memes.append(stored_object)


    def on_data(self, raw_data, return_json=False):
        return super().on_data(raw_data, return_json)

    def on_closed(self, resp):
        print("Stream closed")
        return super().on_closed(resp)

    def search_stream(self, *, backfill_minutes: Optional[int] = None, tweet_fields: Optional[Union[str, List, Tuple]] = None, expansions: Optional[Union[str, List, Tuple]] = None, user_fields: Optional[Union[str, List, Tuple]] = None, media_fields: Optional[Union[str, List, Tuple]] = None, place_fields: Optional[Union[str, List, Tuple]] = None, poll_fields: Optional[Union[str, List, Tuple]] = None, return_json: bool = False):
        return super().search_stream(backfill_minutes = backfill_minutes, tweet_fields = tweet_fields, expansions =expansions, user_fields=user_fields, media_fields=media_fields,place_fields= place_fields,poll_fields= poll_fields,return_json= return_json)


stream = CustomStream(bearer_token=env.get("TWITTER_BEARER_TOKEN"))
if not is_rule_ok:
    reset_rules(stream)

print(stream.get_rules())

@app.get("/get_memes")
async def get_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""

    if last == 0:
        return shuffle_list(new_memes[:max_tweets])
    else:
        # Find the index of the tweetId in the list
        return shuffle_list(new_memes[last : last + max_tweets])

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