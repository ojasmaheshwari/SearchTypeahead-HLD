from collections import defaultdict
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.database import SessionLocal
from ..db.models import Search
from .prefix_utils import get_prefixes
from ..cache.cache_manager import update_suggestions
import logging

logger = logging.getLogger(__name__)

# Track pending updates per query
pending_updates = defaultdict(int)
UPDATE_THRESHOLD = 1000

async def process_cache_updates(query: str):
    """
    1. Fetch current top 10 for each prefix from DB.
    2. Overwrite cache.
    """
    db = SessionLocal()
    try:
        prefixes = get_prefixes(query)
        for prefix in prefixes:
            # Query top 10 for prefix
            top_10 = db.query(Search).filter(Search.query.like(f"{prefix}%")).order_by(text("count * EXP(-0.02 * TIMESTAMPDIFF(HOUR, last_searched, NOW())) DESC")).limit(10).all()
            suggestions = [{"query": s.query, "count": s.count} for s in top_10]
            update_suggestions(prefix, suggestions)
            logger.info(f"[Cache-Update] DB to Cache synchronization complete for prefix: '{prefix}'")
            
    except Exception as e:
        logger.error(f"Error in background cache update for query {query}: {e}")
    finally:
        db.close()

def increment_pending_updates(query: str, increment: int = 1):
    pending_updates[query] += increment
    if pending_updates[query] >= UPDATE_THRESHOLD:
        # Trigger background update
        asyncio.create_task(process_cache_updates(query))
        pending_updates[query] = 0
