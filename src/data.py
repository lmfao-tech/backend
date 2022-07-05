RULES = {
    "add": [
        {
            "value": """(meme OR memes OR humor OR funny) has:images -is:retweet -is:reply lang:en -crypto -nft -politics""",
            "tag": "Funny things",
        },
        {
            "value": """(meme OR memes OR humor OR funny) (tech OR coding OR programming) has:images -is:retweet -is:reply lang:en -crypto -nft -politics""",
            "tag": "Tech",
        },
    ]
}
