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

new_memes_dict: Dict[str, List[StoredObject]] = {"meme_stream": [], "tech_stream": []}
hot_memes_dict = []
hot_last_updated_utc = datetime.utcnow()

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

    if len(new_memes_dict["meme_stream"]) >= 500:
        new_memes_dict["meme_stream"].pop(0)

    stored_object = filter_tweet(tweet)

    if stored_object is None:
        return

    if tweet["matching_rules"][0]["tag"] == "Funny things":
        new_memes_dict["meme_stream"].append(stored_object)
    else:
        new_memes_dict["tech_stream"].append(stored_object)


stream.on_tweet = handle_tweet

if not is_rule_ok:
    reset_rules(stream)


@app.get("/get_memes")
async def get_memes(last: int = 0, max_tweets: int = 20):
    """Get the current memes stored in cache"""
    if last == 0:
        return shuffle_list(new_memes_dict["meme_stream"][:max_tweets])
    else:
        # Find the index of the tweetId in the list
        return shuffle_list(new_memes_dict["meme_stream"][last : last + max_tweets])


@app.get("/hot_memes")
async def hot_memes(last: int = 0, max_tweets: int = 20):
    """Get the hottest memes"""
    global hot_last_updated_utc
    global hot_memes_dict
    if hot_last_updated_utc - datetime.utcnow() > timedelta(hours=1):
        return shuffle_list(hot_memes_dict[:max_tweets])

    since = (datetime.utcnow() - timedelta(hours=random.randint(3, 10))).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    until = (datetime.utcnow() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    memes = api.search_tweets(
        query="meme has:images -is:retweet lang:en -is:reply -contest -instagram -blacksheep -anime -crypto -nft -coins -politics",
        return_json=True,
        max_results=100,
        start_time=since,
        end_time=until,
        tweet_fields=["created_at", "public_metrics"],
        user_fields=[
            "username",
            "name",
            "profile_image_url",
            "created_at",
        ],  # To get the username
        expansions=["attachments.media_keys", "author_id"],
        media_fields=["preview_image_url", "url"],  # To get the image
    )

    # Convert memes into StoredObject[] 
    for index, meme in enumerate(memes["data"]):  # type: ignore
        user_id = meme["author_id"]
        media_key = meme["attachments"]["media_keys"][0]
        meme_link = "https://millenia.tech/logo.png"

        if meme["public_metrics"]["like_count"] < 50:
            continue

        # Find media_key in memes["includes"]["media"]
        for media in memes["includes"]["media"]:  # type: ignore
            if media["media_key"] == media_key:
                meme_link = media["url"]
                break
        
        user = {}
        for user_ in memes["includes"]["users"]:  # type: ignore
            if user_["id"] == user_id:
                user = user_
                break

        stored_obj :StoredObject = {
            "tweet_text": meme["text"],
            "tweet_created_at": meme["created_at"],
            "profile_image_url": user["profile_image_url"],
            "username": user["username"],
            "user": user["name"],
            "user_id": user_id,
            "meme_link": meme_link,
            "tweet_link": f"https://twitter.com/{user['username']}/status/{meme['id']}",
            "tweet_id": meme["id"],
        } 

        hot_memes_dict.append(stored_obj)
        hot_last_updated_utc = datetime.utcnow()

    return hot_memes_dict


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
