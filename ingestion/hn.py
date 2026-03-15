"""Hacker News ingestion — pulls top/new stories via public API."""
import asyncio
import ssl
import certifi
import logging
from datetime import datetime, timezone

import aiohttp

from db import get_conn

logger = logging.getLogger(__name__)

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_NEW_URL = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# How many stories to pull per feed
MAX_STORIES = 50

# Keywords to filter for relevant discussions
KEYWORDS = [
    "ai", "llm", "gpt", "claude", "anthropic", "openai", "mistral",
    "machine learning", "health", "healthcare", "medical",
    "agent", "rag", "embedding", "vector", "prompt",
    "startup", "saas", "devrel", "developer",
]


def _is_relevant(title: str) -> bool:
    """Check if a story title matches our interest keywords."""
    lower = title.lower()
    return any(kw in lower for kw in KEYWORDS)


async def ingest_hn() -> int:
    """Pull relevant stories from HN. Returns count of new posts."""
    new_count = 0
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    try:
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_ctx)
        ) as session:
            # Fetch top + new story IDs
            story_ids = set()
            for url in [HN_TOP_URL, HN_NEW_URL]:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        ids = await resp.json()
                        story_ids.update(ids[:MAX_STORIES])

            logger.info(f"HN: checking {len(story_ids)} stories")

            # Fetch each story
            for story_id in story_ids:
                try:
                    async with session.get(
                        HN_ITEM_URL.format(story_id),
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status != 200:
                            continue
                        item = await resp.json()

                    if not item or item.get("type") != "story":
                        continue

                    title = item.get("title", "")
                    if not _is_relevant(title):
                        continue

                    created = datetime.fromtimestamp(
                        item.get("time", 0), tz=timezone.utc
                    ).isoformat()

                    cur = conn.execute(
                        """INSERT OR IGNORE INTO posts
                           (source, external_id, title, body, author, url,
                            subreddit, score, num_comments, created_at, ingested_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            "hn",
                            str(story_id),
                            title,
                            item.get("text", ""),
                            item.get("by"),
                            item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                            None,
                            item.get("score", 0),
                            item.get("descendants", 0),
                            created,
                            now,
                        ),
                    )
                    if cur.rowcount > 0:
                        new_count += 1

                except Exception as e:
                    logger.warning(f"HN item {story_id} error: {e}")

                await asyncio.sleep(0.1)  # Rate limit

    except Exception as e:
        logger.error(f"HN ingestion error: {e}")

    conn.commit()
    conn.close()
    logger.info(f"HN: {new_count} new relevant posts ingested")
    return new_count
