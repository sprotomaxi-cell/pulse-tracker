"""Reddit ingestion — pulls posts from target subreddits."""
import asyncio
import logging
from datetime import datetime, timezone

import asyncpraw

from config import Config
from db import get_conn

logger = logging.getLogger(__name__)

# Subreddits to track — focused on AI/health tech discussions
TARGET_SUBREDDITS = [
    "artificial",
    "MachineLearning",
    "LocalLLaMA",
    "healthIT",
    "digitalhealth",
    "ChatGPT",
    "ClaudeAI",
]

# How many posts to pull per subreddit
POSTS_PER_SUB = 25


async def ingest_reddit() -> int:
    """Pull recent posts from target subreddits. Returns count of new posts."""
    if not Config.REDDIT_CLIENT_ID:
        logger.warning("Reddit: no credentials set, skipping")
        return 0

    new_count = 0
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()

    reddit = asyncpraw.Reddit(
        client_id=Config.REDDIT_CLIENT_ID,
        client_secret=Config.REDDIT_CLIENT_SECRET,
        user_agent=Config.REDDIT_USER_AGENT,
    )

    try:
        for sub_name in TARGET_SUBREDDITS:
            try:
                subreddit = await reddit.subreddit(sub_name)
                async for post in subreddit.hot(limit=POSTS_PER_SUB):
                    try:
                        cur = conn.execute(
                            """INSERT OR IGNORE INTO posts
                               (source, external_id, title, body, author, url,
                                subreddit, score, num_comments, created_at, ingested_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                "reddit",
                                post.id,
                                post.title,
                                (post.selftext or "")[:5000],
                                str(post.author) if post.author else None,
                                f"https://reddit.com{post.permalink}",
                                sub_name,
                                post.score,
                                post.num_comments,
                                datetime.fromtimestamp(
                                    post.created_utc, tz=timezone.utc
                                ).isoformat(),
                                now,
                            ),
                        )
                        if cur.rowcount > 0:
                            new_count += 1
                    except Exception as e:
                        logger.warning(f"Reddit post insert error: {e}")

                logger.info(f"Reddit r/{sub_name}: fetched {POSTS_PER_SUB} posts")

            except Exception as e:
                logger.error(f"Reddit r/{sub_name} failed: {e}")

            await asyncio.sleep(1)  # Rate limit

    finally:
        await reddit.close()

    conn.commit()
    conn.close()
    logger.info(f"Reddit: {new_count} new posts ingested")
    return new_count
