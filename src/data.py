RULES = {
    "add": [
        {
            "value": """(meme OR memes) has:images -is:retweet lang:en -is:reply -contest -instagram -blacksheep -anime -crypto -nft -coins -politics -comic -comics -roller -furry -manhwa""",
            "tag": "new_memes",
        },
        {
            "value": """(from:weirdrealitymp4 OR from:IntrovertProbss OR from:memesiwish OR from:OldMemeArchive OR from:ManMilk2 OR from:dankmemesreddit OR from:SpongeBobMemesZ OR from:WholesomeMeme OR from:memes OR from:memeadikt) has:images -is:retweet lang:en -is:reply""",
            "tag": "meme_creators",
        }
    ]
}
