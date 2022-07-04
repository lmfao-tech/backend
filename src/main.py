from os import environ as env
import json
from typing import Dict, List

from rich import print
from rich.traceback import install

from dotenv import load_dotenv
from pytwitter import StreamApi
from pytwitter.models import Tweet

from helpers import del_all
from data import RULES

load_dotenv()
install()

is_rule_ok = True

superdict : Dict[str, List[dict]] = {"tweets": []}

# TODO: Replace this with a proper filter
# TODO: Redis as a cache instead of a JSON file
def write_and_stop():
    new_dict = {"tweets": []}
    for i, tweet in enumerate(superdict["tweets"]):
        if "includes" in tweet.keys():
            print(superdict["tweets"][i]["includes"])

            if superdict["tweets"][i]["includes"]['media'][0]['type'] == "photo":
                new_dict["tweets"].append(superdict["tweets"][i])

    with open("superdict.json", "w") as f:
        json.dump(new_dict, f)
    exit()

class CustomStream(StreamApi):

    def __init__(self, *args, **kwargs):
        # TODO: a time limit instead of number of tweets
        self.n = 0
        super().__init__(*args, **kwargs)

    def on_tweet(self, tweet: dict):
        
        if self.n > 100:
            write_and_stop()
    
        superdict["tweets"].append(tweet)
        print(tweet)
        self.n += 1
    
    def on_closed(self, resp):
        return super().on_closed(resp)

    def on_request_error(self, resp):
        print(resp)
        return super().on_request_error(resp)

stream = CustomStream(bearer_token=env.get('TWITTER_BEARER_TOKEN'))

if not is_rule_ok:
    del_all(stream)
    stream.manage_rules(rules=RULES)
    print(stream.get_rules())

stream.search_stream(
    expansions=["attachments.media_keys"], 
    media_fields=["preview_image_url", "url"], # To get the image
    return_json=True # Return JSON because pytwitter doesn't return the `includes` key
)
