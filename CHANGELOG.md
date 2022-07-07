# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- TODO: Replies to celebs are hilarious. Add a filter to add them
- TODO: add popular meme creators (from:WholesomeMeme OR from:JokesMemesFacts OR from:memeadikt OR from:memes OR from:MemesSurreal)


## [0.0.1] - 2022-7-4
### Added
- Dependencies for the project
- Stream for memes with a good (enough) filter
- Save the memes in a JSON file every 100 memes

## [0.0.2] - 2022-7-5
### Added
- Redis as cache
- Flush and reset redis cache according to some conditions
- Helper functions to delete, reset rules and add rules
- Type definitions

### Changed
- Filter to check if the username only has english characters (Solves the problem of many 'foreign' memes and stuff like kpop-specific memes) (TODO: SUPPORT EMOJIS)
- Changed the rules - now also has one for tech memes (TODO: Very few tech memes, somehow increase the frequency)

### Removed
- `images` folder - no longer needed
- JSON storage of memes - replaced by redis
- Unnecessary print statements
  
## [0.0.3] - 2022-7-7
### Added
- Added FASTAPI routes for the memes
- Uvicorn server threaded 
- 

### Removed
- Removed the entire Redis server part - better to have FASTAPI routes so that we can later do more stuff with the API
- The check for username is removed - but there's still a helper function in case we need it