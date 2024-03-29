from typing import Dict, Optional, TypedDict, List
from typing_extensions import NotRequired

Media = TypedDict(
    "Media",
    {
        "type": str,
        "url": str,
        "media_key": str,
    },
)

Rule = TypedDict(
    "Rule",
    {
        "id": int,
        "tag": str,
    },
)

UserObject = TypedDict(
    "UserObject",
    {
        "created_at": str,
        "id": str,
        "name": str,
        "profile_image_url": str,
        "username": str,
    },
)

ReturnedTweetData = TypedDict(
    "ReturnedTweetData",
    {
        "attachments": TypedDict("attachments", {"media_keys": List[str]}),
        "id": str,
        "text": str,
        "author_id": str,
        "created_at": str,
    },
)

urlEntity = TypedDict("url", {"start": int, "end": int, "url": str, "expanded_url": str})


Tweet = TypedDict(
    "tweet",
    {
        "data": TypedDict(
            "data",
            {
                "attachments": TypedDict("attachments", {"media_keys": List[str]}),
                "id": str,
                "text": str,
                "entities": TypedDict("entities", {"urls": List[urlEntity]}),
            },
        ),
        "includes": TypedDict(
            "includes", {"media": List[Media], "users": List[UserObject]}
        ),
        "matching_rules": List[Rule],
    },
)

TweetSearchResult = TypedDict(
    "TweetSearchResult",
    {
        "data": List[ReturnedTweetData],
        "includes": TypedDict(
            "includes", {"media": List[Media], "users": List[UserObject]}
        ),
        "meta": TypedDict("meta", {"result_count": int, "next_token": str}),
    },
)

StoredObject = TypedDict(
    "StoredObject",
    {
        "username": str,
        "user": str,
        "profile_image_url": str,
        "user_id": str,
        "tweet_id": str,
        "tweet_text": str,
        "tweet_link": str,
        "tweet_created_at": str,
        "meme_link": str,
        "source":str,
        "removed_by"  : NotRequired[str],
    },
)
