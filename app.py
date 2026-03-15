"""Flask dashboard — visualize sentiment trends and topic clusters."""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, jsonify

from db import init_db, get_conn

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/overview")
def api_overview():
    """High-level stats."""
    conn = get_conn()
    total_posts = conn.execute("SELECT COUNT(*) as c FROM posts").fetchone()["c"]
    total_analyzed = conn.execute("SELECT COUNT(*) as c FROM sentiments").fetchone()["c"]

    sentiment_dist = {}
    for row in conn.execute(
        "SELECT sentiment, COUNT(*) as c FROM sentiments GROUP BY sentiment"
    ):
        sentiment_dist[row["sentiment"]] = row["c"]

    sources = {}
    for row in conn.execute(
        "SELECT source, COUNT(*) as c FROM posts GROUP BY source"
    ):
        sources[row["source"]] = row["c"]

    conn.close()
    return jsonify({
        "total_posts": total_posts,
        "total_analyzed": total_analyzed,
        "sentiment_distribution": sentiment_dist,
        "sources": sources,
    })


@app.route("/api/trends")
def api_trends():
    """Sentiment over time (last 7 days, grouped by day)."""
    conn = get_conn()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    rows = conn.execute(
        """SELECT
             DATE(p.created_at) as day,
             s.sentiment,
             COUNT(*) as count
           FROM sentiments s
           JOIN posts p ON p.id = s.post_id
           WHERE p.created_at > ?
           GROUP BY day, s.sentiment
           ORDER BY day""",
        (cutoff,),
    ).fetchall()
    conn.close()

    # Reshape into {day: {positive: N, negative: N, ...}}
    trends = {}
    for row in rows:
        day = row["day"]
        if day not in trends:
            trends[day] = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        trends[day][row["sentiment"]] = row["count"]

    return jsonify(trends)


@app.route("/api/topics")
def api_topics():
    """Top topics by post count."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT name, post_count FROM topics ORDER BY post_count DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify([{"name": r["name"], "count": r["post_count"]} for r in rows])


@app.route("/api/posts")
def api_posts():
    """Recent analyzed posts with sentiment."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT p.title, p.source, p.subreddit, p.url, p.score, p.num_comments,
                  p.created_at, s.sentiment, s.confidence, s.topics, s.summary
           FROM sentiments s
           JOIN posts p ON p.id = s.post_id
           ORDER BY p.created_at DESC
           LIMIT 50"""
    ).fetchall()
    conn.close()

    posts = []
    for r in rows:
        posts.append({
            "title": r["title"],
            "source": r["source"],
            "subreddit": r["subreddit"],
            "url": r["url"],
            "score": r["score"],
            "num_comments": r["num_comments"],
            "created_at": r["created_at"],
            "sentiment": r["sentiment"],
            "confidence": r["confidence"],
            "topics": json.loads(r["topics"]) if r["topics"] else [],
            "summary": r["summary"],
        })

    return jsonify(posts)


@app.route("/api/topic-sentiment")
def api_topic_sentiment():
    """Sentiment breakdown per topic."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT s.topics, s.sentiment
           FROM sentiments s
           WHERE s.topics IS NOT NULL"""
    ).fetchall()
    conn.close()

    topic_sentiments = {}
    for row in rows:
        topics = json.loads(row["topics"]) if row["topics"] else []
        for topic in topics:
            if topic not in topic_sentiments:
                topic_sentiments[topic] = Counter()
            topic_sentiments[topic][row["sentiment"]] += 1

    # Top 15 topics by total mentions
    sorted_topics = sorted(
        topic_sentiments.items(), key=lambda x: sum(x[1].values()), reverse=True
    )[:15]

    return jsonify({
        topic: dict(counts) for topic, counts in sorted_topics
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5050)
