from typing import Dict, TypedDict, List

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

Tweet = TypedDict(
    "tweet",
    {
        "data": TypedDict(
            "data",
            {
                "attachments": TypedDict("attachments", {"media_keys": List[str]}),
                "id": str,
                "text": str,
            },
        ),
        "includes": TypedDict("includes", {"media": List[Media], "users": List[UserObject]}),
        "matching_rules": List[Rule],
    },
)

StoredObject = TypedDict(
    "StoredObject",
    {
        "username": str,
        "user":str,
        "profile_image_url": str,
        "tweet_id": str,
        "tweet_text": str,
        "tweet_link":str,
        "tweet_created_at": str,
        "meme_link": str,
    }
)