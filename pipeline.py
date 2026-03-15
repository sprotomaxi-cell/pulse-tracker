"""Pipeline orchestrator — ingest, analyze, report."""
import asyncio
import logging
import sys

from db import init_db
from ingestion.reddit import ingest_reddit
from ingestion.hn import ingest_hn
from analysis import analyze_unscored

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("pulse")


async def run():
    logger.info("=" * 40)
    logger.info("Pulse pipeline starting")
    logger.info("=" * 40)

    # 1. Init DB
    init_db()

    # 2. Ingest from all sources
    reddit_count, hn_count = await asyncio.gather(
        ingest_reddit(),
        ingest_hn(),
    )
    logger.info(f"Ingestion complete: {reddit_count} Reddit, {hn_count} HN new posts")

    # 3. Analyze sentiment on new posts
    analyzed = await analyze_unscored(batch_size=30)
    logger.info(f"Analysis complete: {analyzed} posts analyzed")

    logger.info("Done.")


if __name__ == "__main__":
    asyncio.run(run())
