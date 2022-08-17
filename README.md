![LMFAO.tech logomark](https://lmfao.tech/og-image.png)

[Website](https://lmfao.tech) |  [What is LMFAO.tech?](https://what-is.lmfao.tech)

## Inspiration
Memes are an essential part of the internet culture - they are everywhere.

Whether that's good or bad, there’s no denying that memes have revolutionized the way we communicate. Millions of memes are shared on Twitter and other social media platforms daily.
Ever wanted to sit back, relax, and scroll through some memes? 

We can relate.
This world is a sack of all sorts of entertaining content, but when it comes to sorting high-quality and original memes or creating them, most platforms fail to do that.

Well, no more!
Where your time and smile are precious, and your creativity feeds your and others' happiness, we come in with LMFAO.tech

## What it does

With an aim to make you go LMFAO or at least put a smile on your face, we created LMFAO. tech - A meme discovery and creation platform.

LMFAO (which stands for laughing my f*cking *ss out)  is a meme platform targeted at people who browse Twitter primarily for memes. An algorithm uses the Twitter filtered search stream to get memes which are featured in the “Home” tab, after some software filters, NSFW checks and more

Users have the ability to interact with posts on the home tab, provided that they have already logged into the app using their Twitter account. Liking/retweeting the posts, and creating posts also use the Twitter APIv2 to do the same on Twitter. Consequently, the receiver of the like gets some LMFAO coins for it. In exchange for this activity, the user who likes the posts also gets a coin. This is done in order to incentivize user activity and the act of liking posts. 

Users can also create or publish posts, that will be tweeted using their own (currently logged in) Twitter account. Users can also gain points by posting. A tweet is created with a mention to the Twitter bot, [@LMFAO_tech](https://twitter.com/lmfao_tech)

## Overview

### Main page
The main (home) page pulls memes ONLY from the community.

These can be:
- Memes uploaded *through* LMFAO.tech
- Memes found by our community and pushed using the [@LMFAO_tech](https://twitter.com/LMFAO_tech) bot on Twitter

### Explore page
The backend pulls the latest memes from Twitter via a Filtered search stream. After a lot of checks and filters, They are shown on this page.

## How we built it
The app was built with

- **ReactJS** - javascript library for building user interfaces
- **NextJS** is our fast React framework for performance, scalability, security, and accessibility. The serverless API routes in the app are able to handle the heavy-lifting of all user’s calls (liking, retweeting, posting) to the Twitter API
- **Typescript** for strongly-typed codebase and catching errors early.
- **TailwindCSS** to leverage benefits and speed of utility-first CSS framework
- **TwitterAPI** provides the entire infrastructure over which LMFAO.tech is built upon. Authorization, Database, Liking/Retweeting/Posting, everything is powered by TwitterAPI v2
- **Novu** provides the notification infrastructure for the users.
- **PlanetScale’s MySQL database** to store the points, user information like username, userID
- **Redis** hosted on RedisCloud for providing fast read and write of the meme cache and community memes
- **Prisma** as the ORM to interact with the database
- **Framer-Motion** for animations on the main page
- **Python with FastAPI** as a fast and reliable backend server
- **Vercel** for hosting the Frontend
- **Railway** for hosting everything else (Backend, Coins distributor, Twitter bot)

This is the overall structure of how it works

![Untitled](https://s3-us-west-2.amazonaws.com/secure.notion-static.com/79229994-b8bf-4379-acb3-df3176b54809/Untitled.png)

## Overview

### Main page
The main page has memes that are submitted by the community.
This includes:
- Memes uploaded/created *through* LMFAO.tech
- Memes found by our community and pushed using the [@LMFAO_tech](https://twitter.com/LMFAO_tech) bot on Twitter

### Explore page
This is the automated feed. The backend streams posts using the Twitter Filtered search stream and the posts appear here after our checks, filters and moderation.

### Dashboard page
See your position among the crowd, how many coins you have, and the global leaderboard

### Profile page

A single page for all your memes and statistics

### Create page

Create page is the one page where you can create and publish memes. This is the page with the meme creator and the template picker. Here’s a GIF
![Create page](https://us-east-1.tixte.net/uploads/i.dhr.wtf/l6sd84yfw5c.gif)

### Notifications

Notifications tab, for the dopamine! Whenever you get a like/follow through LMFAO.tech, you get a notification for it. Powered by Novu
![notifications](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/9e1fa4ab-d78e-42a8-b62c-fcc3d8bd6c37/Untitled.png)

### Twitter bot

The Twitter bot serves multiple purposes:

- Discover memes that will be submitted by the community. Anyone can mention the bot under any post and get rewarded for their contribution to the community.
Did you find a meme that made you laugh? Mention the bot! Helps the community and you earn points for it. 
- Allow users to publish their own memes to the community (By tagging the bot in the main tweet itself)

## Main callout features

- Ships as a Progressive web app - Offline loading, Multi-device native-like feel
- Notifications for all interactions
- Blazingly fast meme loading - Powered by a Redis database
- Multiple streams for memes - Main tab, the community tab
- Advanced moderation features for select users. “Supermod” features for the makers
- Points, Leaderboard, Ranks and streaks system integrated into the functionality that makes everything fun!
- Advanced meme maker with the option to select predefined meme templates. Also an option to google image search right in the meme template picker

## Challenges we ran into
This was the first actual product made by my brother (DhravyaShah) and his friend (Yash). The branding and design of the app were definitely a challenge. 

At first, we had some trouble with authorizing users into our app - NextAuth didn't have the customizability we needed, so we tried to come up with a custom solution.
However, in the end, with some help with friends, we were able to implement good and reliable auth. using the Twitter Oauth1

We also had trouble implementing the meme maker, but we were able to make it really good in a short time. Uploading memes through our app was also a challenge, because it was media, and we weren't quite sure how we could implement it using APIv2. 
We wanted to complete the Chrome extension but couldn't because of our team's inexperience in the domain.

In the backend, we were having issues with the content quality of the automated stream of memes.

## Accomplishments that we're proud of
We were able to create a community platform with a pretty good launch on ProductHunt. The meme maker was also a challenge that we figure out how to solve.
Even though we haven't perfected yet, we are really proud of the automated stream right now. We had to implement a moderation system along with it, but it's done now and works perfectly!

We are also proud of implementing the notifications feature really quickly and effectively. 

## What we learned
We learned a lot through this challenge. The importance of branding, community, moderation of content, etc were things we learned for the first time. We had 2 young developers in our team (who couldn't participate in the hackathon because of the rules) who managed to do most of the implementation of the app.
We also learnt how to make good PWAs (progressive web apps), and will be launching the app on the google play store (soon!). Since this was our first product, we had no idea how to advertise or launch to product hunt effectively, and even though our launch wasn't perfect with a lot of competition that day, we learnt a lot!

## Possible monetisation strategy

The primary objective of [LMFAO.tech](http://LMFAO.tech) is not to make money but provide a nice UI and community, along with some amazing features that make the users’ days 1% better by at least bringing a smile to their faces. However, we realized that there were possible monetisation strategies.

We could show some ads in the app itself - ads that integrate with the user interface. It is also possible to show meme-based ads that the target audience may have a higher chance to click on. With 10,000 users per month, ads could earn us around $100. The total cost of hosting all our infrastructure is about $10 as of right now, but we expect it to increase to about 50$ as users increase. This will help us cover the server costs as well as some coffee for developers!

Another option we thought of was a premium subscription. If we provide enough good features and a better experience for premium users, we could charge about 2$ a month. This would help us cover hosting charges with just 5 premium users.

## What's next for LMFAO.tech
Although this hackathon took part over a span of months, we would have loved to ship more features that we didn’t have time for. We intend to keep working on this project as a team after the hackathon has ended. The following is a list of some of the extensions we would like to implement next:

- A chrome extension with which users can click on a button on the tweet to post to LMFAO.tech
- Use RedisSearch to quickly search through our community memes
- Integrate with more apps like Reddit and Instagram using our same filter technology to have more content for our users
- We would like to add alternate sign-in methods that would be used for posting memes. However, liking won’t work

## Frequently asked questions

- What is the coins system?
    
    Every day, each user gets to like 50 posts (HAHA coins). For every post they like, they get 1 LMFAO coin and the receiver gets 5 coins.
    

- Why can’t I log in with other providers?
    
    Some core functionality of the app - retweeting, liking, and publishing memes require the user to be logged in. This is because the posts are also liked, retweeted and published on twitter (Which is then pulled by our bot)
    

- What is the Community tab? 👥
    
    The community tab is one made JUST for memes *chosen, created or posted* by the members of LMFAO.tech. Unlike the main page, memes aren’t pulled from all across twitter - just ones that tag @LMFAO_tech twitter account.
