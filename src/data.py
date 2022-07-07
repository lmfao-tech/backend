RULES = {
    "add": [
        {
            "value": """(meme OR memes OR humor OR funny) has:images -is:retweet lang:en -crypto -nft -politics""",
            "tag": "Funny things",
        },
        {
            "value": """((tech meme) OR (coding meme) OR (programming meme)) has:images -is:retweet -is:reply lang:en -crypto -nft -politics""",
            "tag": "Tech",
        },
    ]
}
