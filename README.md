# Pulse

Real-time sentiment analysis of AI and health tech discussions across Reddit and Hacker News.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![Claude](https://img.shields.io/badge/Claude_AI-Haiku-purple)

## What it does

Pulse ingests public discussions from Reddit and Hacker News, classifies sentiment using Claude AI, and surfaces trends through a live dashboard. It tracks what people actually think about AI tools, health tech products, and developer platforms.

**Pipeline:**
1. **Ingest** — Async scrapers pull posts from target subreddits and HN (keyword-filtered)
2. **Analyze** — Claude Haiku classifies each post: sentiment, confidence, topics, one-line summary
3. **Visualize** — Flask dashboard with sentiment trends, topic breakdowns, and post feed

## Architecture

```
Reddit API ──┐
             ├── async pipeline ── Claude AI ── SQLite ── Flask dashboard
HN API ──────┘
```

- **Async Python** throughout (aiohttp, asyncpraw)
- **Claude Haiku** for fast, cheap sentiment classification (~$0.001/post)
- **SQLite** with WAL mode for concurrent reads/writes
- **Chart.js** for interactive trend visualization

## Quick Start

```bash
git clone https://github.com/sprotomaxi-cell/pulse-tracker.git
cd pulse-tracker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# Run the pipeline
python pipeline.py

# Start the dashboard
python app.py  # http://localhost:5050
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/overview` | Total posts, sentiment distribution, source counts |
| `GET /api/trends` | Sentiment by day (last 7 days) |
| `GET /api/topics` | Top 20 topics by frequency |
| `GET /api/topic-sentiment` | Sentiment breakdown per topic |
| `GET /api/posts` | Recent 50 analyzed posts with metadata |

## Configuration

**Required:**
- `ANTHROPIC_API_KEY` — for Claude sentiment analysis

**Optional:**
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — for Reddit ingestion ([create app here](https://www.reddit.com/prefs/apps))
- HN ingestion works without auth

## Tech Stack

Python, Flask, aiohttp, asyncpraw, Anthropic SDK, SQLite, Chart.js
