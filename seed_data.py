"""Seed the database with realistic sample data for demo purposes."""
import json
import random
from datetime import datetime, timedelta, timezone

from db import init_db, get_conn

SAMPLE_POSTS = [
    # Positive AI discussions
    {"title": "Claude 4.5 Sonnet is genuinely impressive for code generation", "source": "reddit", "sub": "ClaudeAI", "sentiment": "positive", "confidence": 0.92, "topics": ["claude ai", "code generation"], "summary": "User shares positive experience with Claude 4.5 for production code tasks."},
    {"title": "We replaced our entire QA pipeline with LLM-based testing", "source": "hn", "sub": None, "sentiment": "positive", "confidence": 0.85, "topics": ["llm testing", "qa automation"], "summary": "Team reports 60% reduction in QA time after switching to LLM-based test generation."},
    {"title": "Open-source medical LLM outperforms GPT-4 on clinical reasoning benchmarks", "source": "reddit", "sub": "MachineLearning", "sentiment": "positive", "confidence": 0.88, "topics": ["healthcare ai", "open-source models", "clinical reasoning"], "summary": "New open-source model achieves state-of-the-art results on medical reasoning tasks."},
    {"title": "My experience deploying RAG in production for 6 months", "source": "hn", "sub": None, "sentiment": "positive", "confidence": 0.78, "topics": ["rag systems", "production deployment"], "summary": "Developer shares lessons learned from running RAG in production, mostly positive outcomes."},
    {"title": "Anthropic's new safety research is actually pushing capabilities forward", "source": "reddit", "sub": "artificial", "sentiment": "positive", "confidence": 0.82, "topics": ["ai safety", "anthropic"], "summary": "Discussion of how safety-focused research at Anthropic has led to capability improvements."},
    {"title": "Digital health startup just got FDA clearance for AI diagnostic tool", "source": "reddit", "sub": "digitalhealth", "sentiment": "positive", "confidence": 0.90, "topics": ["healthcare ai", "fda approval", "diagnostics"], "summary": "AI diagnostic tool receives FDA 510(k) clearance for detecting lung nodules."},
    {"title": "LangChain finally simplified their API and it actually makes sense now", "source": "reddit", "sub": "LocalLLaMA", "sentiment": "positive", "confidence": 0.75, "topics": ["langchain", "developer experience"], "summary": "Users praise recent LangChain API redesign for improved developer experience."},
    {"title": "We built a health data pipeline that processes 2M records daily with Claude", "source": "hn", "sub": None, "sentiment": "positive", "confidence": 0.86, "topics": ["data pipelines", "healthcare ai", "claude ai"], "summary": "Health tech company describes their Claude-powered data processing architecture."},
    {"title": "Show HN: AI-powered EHR summarization tool for clinicians", "source": "hn", "sub": None, "sentiment": "positive", "confidence": 0.88, "topics": ["ehr systems", "healthcare ai", "clinical tools"], "summary": "New tool uses AI to summarize electronic health records for faster clinical review."},
    {"title": "The Muse job board API is surprisingly good for building recruitment tools", "source": "hn", "sub": None, "sentiment": "positive", "confidence": 0.72, "topics": ["job boards", "api design", "developer tools"], "summary": "Developer praises The Muse API design for job search application development."},

    # Negative discussions
    {"title": "AI hallucinations in healthcare are going to kill someone", "source": "reddit", "sub": "healthIT", "sentiment": "negative", "confidence": 0.91, "topics": ["ai safety", "healthcare ai", "hallucinations"], "summary": "Healthcare IT professional warns about risks of deploying unvalidated AI in clinical settings."},
    {"title": "OpenAI's pricing changes are pushing small startups out of the market", "source": "hn", "sub": None, "sentiment": "negative", "confidence": 0.84, "topics": ["openai", "api pricing", "startups"], "summary": "Founders discuss how recent OpenAI price increases are forcing them to find alternatives."},
    {"title": "LLM coding assistants are making junior devs worse at debugging", "source": "reddit", "sub": "artificial", "sentiment": "negative", "confidence": 0.76, "topics": ["coding assistants", "developer skills", "ai dependency"], "summary": "Discussion about whether AI coding tools are creating a generation of developers who cannot debug."},
    {"title": "Hospital IT departments are completely unprepared for AI integration", "source": "reddit", "sub": "healthIT", "sentiment": "negative", "confidence": 0.88, "topics": ["healthcare ai", "hospital it", "implementation challenges"], "summary": "IT manager describes the gap between AI vendor promises and hospital infrastructure reality."},
    {"title": "Most RAG implementations I've seen are barely better than keyword search", "source": "hn", "sub": None, "sentiment": "negative", "confidence": 0.79, "topics": ["rag systems", "search quality"], "summary": "Engineer argues that poorly implemented RAG systems add complexity without improving results."},
    {"title": "The AI developer tools market is becoming impossibly crowded", "source": "hn", "sub": None, "sentiment": "negative", "confidence": 0.73, "topics": ["ai tooling", "market saturation", "startups"], "summary": "Discussion about oversaturation in the AI dev tools space and looming consolidation."},

    # Neutral / Mixed
    {"title": "Comparing embedding models for clinical text: what actually matters", "source": "reddit", "sub": "MachineLearning", "sentiment": "neutral", "confidence": 0.81, "topics": ["embeddings", "clinical text", "model comparison"], "summary": "Technical comparison of embedding models for healthcare NLP applications."},
    {"title": "Ask HN: How is AI-assisted coding going for you professionally?", "source": "hn", "sub": None, "sentiment": "mixed", "confidence": 0.68, "topics": ["coding assistants", "developer productivity"], "summary": "Mixed responses from developers about AI coding tool adoption in professional settings."},
    {"title": "The state of health informatics job market in 2026", "source": "reddit", "sub": "healthIT", "sentiment": "mixed", "confidence": 0.72, "topics": ["health informatics", "job market", "career trends"], "summary": "Discussion shows growing demand for health informatics roles but competition from AI automation."},
    {"title": "Vector databases in 2026: Pinecone vs pgvector vs Weaviate", "source": "hn", "sub": None, "sentiment": "neutral", "confidence": 0.85, "topics": ["vector databases", "infrastructure"], "summary": "Technical comparison of vector database options for production RAG systems."},
    {"title": "Prompt engineering is becoming a legitimate engineering discipline", "source": "reddit", "sub": "artificial", "sentiment": "mixed", "confidence": 0.71, "topics": ["prompt engineering", "ai careers"], "summary": "Debate about whether prompt engineering is a real skill or temporary artifact of current AI limitations."},
    {"title": "HIPAA compliance guide for AI-powered health applications", "source": "reddit", "sub": "digitalhealth", "sentiment": "neutral", "confidence": 0.90, "topics": ["hipaa", "healthcare ai", "compliance"], "summary": "Comprehensive guide to navigating HIPAA requirements when building AI health tools."},
    {"title": "Why we switched from LangChain to building our own orchestration layer", "source": "hn", "sub": None, "sentiment": "mixed", "confidence": 0.74, "topics": ["langchain", "ai orchestration", "build vs buy"], "summary": "Team explains tradeoffs of using LangChain versus custom orchestration for production AI."},
    {"title": "Mistral Large 2 vs Claude 3.5 Sonnet for structured data extraction", "source": "reddit", "sub": "LocalLLaMA", "sentiment": "neutral", "confidence": 0.83, "topics": ["mistral", "claude ai", "data extraction"], "summary": "Benchmark comparison of Mistral and Claude for JSON extraction from unstructured documents."},
    {"title": "The hidden costs of running AI in healthcare nobody talks about", "source": "reddit", "sub": "digitalhealth", "sentiment": "negative", "confidence": 0.80, "topics": ["healthcare ai", "operational costs", "implementation challenges"], "summary": "Healthcare exec details unexpected costs of AI deployment including training, validation, and monitoring."},
    {"title": "Async Python patterns for high-throughput data pipelines", "source": "hn", "sub": None, "sentiment": "positive", "confidence": 0.77, "topics": ["async python", "data pipelines", "performance"], "summary": "Tutorial on using asyncio patterns for building efficient data processing pipelines."},
    {"title": "Wearable health data is the next frontier for preventive AI", "source": "reddit", "sub": "digitalhealth", "sentiment": "positive", "confidence": 0.84, "topics": ["wearable health", "preventive care", "health data"], "summary": "Researchers argue that continuous wearable data will enable AI-driven preventive health interventions."},
    {"title": "We need to talk about AI agent reliability in production", "source": "hn", "sub": None, "sentiment": "negative", "confidence": 0.82, "topics": ["ai agents", "production reliability", "observability"], "summary": "Engineer describes cascading failures in production AI agent systems and calls for better tooling."},
    {"title": "Flask vs FastAPI for AI-powered web apps in 2026", "source": "reddit", "sub": "artificial", "sentiment": "neutral", "confidence": 0.69, "topics": ["flask", "fastapi", "web frameworks"], "summary": "Comparison of web frameworks for serving AI-powered applications."},
    {"title": "The real bottleneck in clinical AI is data interoperability, not models", "source": "hn", "sub": None, "sentiment": "mixed", "confidence": 0.87, "topics": ["clinical ai", "data interoperability", "healthcare infrastructure"], "summary": "Discussion argues that healthcare AI progress is limited by fragmented data systems, not model quality."},
]


def seed():
    init_db()
    conn = get_conn()
    now = datetime.now(timezone.utc)

    for i, post in enumerate(SAMPLE_POSTS):
        # Spread posts across the last 7 days
        days_ago = random.uniform(0, 7)
        created = (now - timedelta(days=days_ago)).isoformat()
        ingested = (now - timedelta(days=days_ago - 0.01)).isoformat()

        ext_id = f"seed_{i}"
        score = random.randint(20, 500)
        comments = random.randint(5, 200)

        cur = conn.execute(
            """INSERT OR IGNORE INTO posts
               (source, external_id, title, body, author, url, subreddit,
                score, num_comments, created_at, ingested_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                post["source"],
                ext_id,
                post["title"],
                "",
                "user_" + str(random.randint(100, 999)),
                f"https://example.com/{ext_id}",
                post.get("sub"),
                score,
                comments,
                created,
                ingested,
            ),
        )

        if cur.lastrowid and cur.rowcount > 0:
            conn.execute(
                """INSERT OR IGNORE INTO sentiments
                   (post_id, sentiment, confidence, topics, summary, analyzed_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cur.lastrowid,
                    post["sentiment"],
                    post["confidence"],
                    json.dumps(post["topics"]),
                    post["summary"],
                    ingested,
                ),
            )

            for topic in post["topics"]:
                conn.execute(
                    """INSERT INTO topics (name, first_seen, post_count)
                       VALUES (?, ?, 1)
                       ON CONFLICT(name) DO UPDATE SET
                         post_count = post_count + 1""",
                    (topic, ingested),
                )

    conn.commit()
    conn.close()
    print(f"Seeded {len(SAMPLE_POSTS)} posts with sentiment data")


if __name__ == "__main__":
    seed()
