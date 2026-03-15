"""Sentiment analysis — uses Claude to classify posts."""
import json
import logging
from datetime import datetime, timezone

import anthropic

from config import Config
from db import get_conn

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a sentiment analysis engine. Analyze the given post and return a JSON object with:

{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "confidence": 0.0-1.0,
  "topics": ["topic1", "topic2"],
  "summary": "One sentence summary of the post's main point"
}

Topics should be specific and descriptive (e.g., "LLM reliability", "healthcare AI adoption", "open-source models").
Keep topics lowercase. Return 1-3 topics per post.
Return ONLY valid JSON, no other text."""


async def analyze_unscored(batch_size: int = 20) -> int:
    """Analyze posts that haven't been scored yet. Returns count analyzed."""
    if not Config.ANTHROPIC_API_KEY:
        logger.warning("No Anthropic API key set, skipping analysis")
        return 0

    conn = get_conn()
    rows = conn.execute(
        """SELECT p.id, p.title, p.body, p.source, p.subreddit
           FROM posts p
           LEFT JOIN sentiments s ON s.post_id = p.id
           WHERE s.id IS NULL
           ORDER BY p.ingested_at DESC
           LIMIT ?""",
        (batch_size,),
    ).fetchall()

    if not rows:
        logger.info("No unanalyzed posts")
        conn.close()
        return 0

    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    analyzed = 0
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        title = row["title"] or ""
        body = (row["body"] or "")[:2000]
        source = row["source"]
        sub = f" (r/{row['subreddit']})" if row["subreddit"] else ""

        user_msg = f"Source: {source}{sub}\nTitle: {title}\n\n{body}".strip()

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )

            text = response.content[0].text.strip()
            # Handle markdown code blocks
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            result = json.loads(text)

            conn.execute(
                """INSERT OR IGNORE INTO sentiments
                   (post_id, sentiment, confidence, topics, summary, analyzed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    row["id"],
                    result.get("sentiment", "neutral"),
                    result.get("confidence", 0.5),
                    json.dumps(result.get("topics", [])),
                    result.get("summary", ""),
                    now,
                ),
            )

            # Update topic counts
            for topic in result.get("topics", []):
                conn.execute(
                    """INSERT INTO topics (name, first_seen, post_count)
                       VALUES (?, ?, 1)
                       ON CONFLICT(name) DO UPDATE SET
                         post_count = post_count + 1""",
                    (topic.lower(), now),
                )

            analyzed += 1

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error for post {row['id']}: {e}")
        except Exception as e:
            logger.error(f"Analysis failed for post {row['id']}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"Analyzed {analyzed}/{len(rows)} posts")
    return analyzed
