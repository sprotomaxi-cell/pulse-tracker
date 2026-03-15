"""Sentiment analysis — tries Ollama (free, local) first, falls back to Claude."""
import json
import logging
from datetime import datetime, timezone

import aiohttp
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

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

# Module-level flag so we only warn once per run if Ollama is down
_ollama_available: bool | None = None


def _build_ollama_prompt(user_msg: str) -> str:
    """Combine system instructions and user message into a single prompt."""
    return f"{SYSTEM_PROMPT}\n\n---\n\n{user_msg}"


async def _call_ollama(user_msg: str) -> dict | None:
    """Try to get a sentiment result from Ollama. Returns parsed dict or None."""
    global _ollama_available

    # If we already know Ollama is unreachable this run, skip it
    if _ollama_available is False:
        return None

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": _build_ollama_prompt(user_msg),
        "stream": False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OLLAMA_URL, json=payload, timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Ollama returned status %d, falling back to Claude", resp.status
                    )
                    _ollama_available = False
                    return None

                data = await resp.json()
                text = data.get("response", "").strip()

                # Handle markdown code blocks
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

                result = json.loads(text)
                _ollama_available = True
                return result

    except (aiohttp.ClientError, OSError):
        # Ollama not running or unreachable
        if _ollama_available is not False:
            logger.info("Ollama not available at %s, falling back to Claude", OLLAMA_URL)
            _ollama_available = False
        return None
    except json.JSONDecodeError as e:
        logger.warning("Ollama returned invalid JSON: %s", e)
        return None


def _call_claude(client: anthropic.Anthropic, user_msg: str) -> dict:
    """Get sentiment result from Claude. Raises on failure."""
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

    return json.loads(text)


async def analyze_unscored(batch_size: int = 20) -> int:
    """Analyze posts that haven't been scored yet. Returns count analyzed."""
    global _ollama_available

    # Reset availability check each batch so we retry if Ollama comes back up
    _ollama_available = None

    has_claude = bool(Config.ANTHROPIC_API_KEY)

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

    client = (
        anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY) if has_claude else None
    )
    analyzed = 0
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        title = row["title"] or ""
        body = (row["body"] or "")[:2000]
        source = row["source"]
        sub = f" (r/{row['subreddit']})" if row["subreddit"] else ""

        user_msg = f"Source: {source}{sub}\nTitle: {title}\n\n{body}".strip()

        try:
            # Try Ollama first (free, local)
            result = await _call_ollama(user_msg)

            # Fall back to Claude if Ollama didn't work
            if result is None:
                if client is None:
                    logger.warning(
                        "Neither Ollama nor Claude available, skipping analysis"
                    )
                    break
                result = _call_claude(client, user_msg)

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

    backend = "Ollama" if _ollama_available else "Claude"
    logger.info(f"Analyzed {analyzed}/{len(rows)} posts via {backend}")
    return analyzed
