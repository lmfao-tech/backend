RULES = {
    "add": [
        {
            "value": """(meme OR memes OR humor OR funny OR joke) has:images -is:retweet lang:en -is:reply -contest -instagram -blacksheep -anime -crypto -nft -coins -politics""",
            "tag": "Funny things",
        },
        {
            "value": """((tech meme) OR (coding meme) OR (programming meme)) has:images -is:retweet -is:reply lang:en -crypto -nft -politics""",
            "tag": "Tech",
        },
    ]
}
