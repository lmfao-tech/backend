import json
import random
from random import random
from typing import List, Dict
from os import environ as env

from rich import print
from dotenv import load_dotenv
from pytwitter import StreamApi
from rich.traceback import install
from datetime import datetime, timedelta

from db import connect_to_redis
from helpers import reset_rules
from _types import Tweet, StoredObject

load_dotenv()
install()

redis_client = connect_to_redis()

# If set to false, it will delete all the rules and use the RULES from src\data.py
is_rule_ok = True

last_updated = datetime.now()

super_dict: Dict[str, List[StoredObject]] = {"meme_stream": [], "tech_stream": []}

stream = StreamApi(bearer_token=env.get("TWITTER_BEARER_TOKEN"))

print("[green]Starting stream[/green]")
print(stream.get_rules())


def handle_tweet(tweet: Tweet):

    global last_updated
    if datetime.now() - last_updated > timedelta(minutes=5):
        flush_and_reset()
        last_updated = datetime.now()

    created_at = datetime.strptime(
        tweet["includes"]["users"][0]["created_at"], "%Y-%m-%dT%H:%M:%S.000Z"
    )

    # If the created_at is less than one month ago, it will not be saved
    if created_at > datetime.now() - timedelta(days=30):
        return
    if not "media" in tweet["includes"]:
        return
    if not tweet["includes"]["media"][0]["type"] == "photo":
        return

    # Check if tweet["includes"]["users"][0]["name"] contains english characters only
    if not all(ord(c) < 128 for c in tweet["includes"]["users"][0]["name"]):
        return

    stored_object: StoredObject = {
        "username": tweet["includes"]["users"][0]["username"],
        "user": tweet["includes"]["users"][0]["name"],
        "profile_image_url": tweet["includes"]["users"][0]["profile_image_url"],
        "tweet_id": tweet["data"]["id"],
        "tweet_text": tweet["data"]["text"],
        "tweet_link": f"https://twitter.com/{tweet['includes']['users'][0]['username']}/status/{tweet['data']['id']}",
        "tweet_created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "meme_link": tweet["includes"]["media"][0]["url"],
    }

    print(tweet["matching_rules"][0]["tag"])
    if tweet["matching_rules"][0]["tag"] == "Funny things":
        super_dict["meme_stream"].append(stored_object)
    elif tweet["matching_rules"][0]["id"] == "1544187580954349569":
        print(stored_object)
        super_dict["tech_stream"].append(stored_object)


def flush_and_reset():

    # delete meme_Stream
    redis_client.delete("meme_stream")
    print("[green]Flushed memes database[/green]")
    redis_client.set("meme_stream", json.dumps(super_dict["meme_stream"]))
    print("[green]Saved memes to redis[/green]")

    if random.randint(0, 1) == 1:
        # delete tech_Stream
        redis_client.delete("tech_stream")
        print("[green]Flushed tech database[/green]")
        redis_client.set("tech_stream", json.dumps(super_dict["tech_stream"]))
        print("[green]Saved tech to redis[/green]")


stream.on_tweet = handle_tweet

if not is_rule_ok:
    reset_rules(stream)

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
