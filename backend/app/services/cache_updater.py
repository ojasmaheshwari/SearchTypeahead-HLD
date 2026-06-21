import asyncio
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.database import SessionLocal
from ..db.models import Search
from .prefix_utils import get_prefixes
from ..cache.cache_manager import update_suggestions
import logging

logger = logging.getLogger(__name__)

# Track pending updates globally
pending_updates = defaultdict(int)
total_pending = 0
UPDATE_THRESHOLD = 1000
lock = asyncio.Lock()

async def flush_to_db_and_cache():
    global pending_updates, total_pending
    
    current_updates = pending_updates
    pending_updates = defaultdict(int)
    total_pending = 0
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _flush_sync, current_updates)

def _flush_sync(current_updates):
    if not current_updates:
        return
        
    db = SessionLocal()
    try:
        # DB Update
        existing_searches = db.query(Search).filter(Search.query.in_(current_updates.keys())).all()
        existing_queries = {s.query: s for s in existing_searches}
        
        new_records = []
        for q, count in current_updates.items():
            if q in existing_queries:
                existing_queries[q].count += count
            else:
                new_records.append(Search(query=q, count=count))
                
        if new_records:
            db.add_all(new_records)
            
        db.commit()
        
        # Cache Update
        affected_prefixes = set()
        for q in current_updates.keys():
            for p in get_prefixes(q):
                affected_prefixes.add(p)
            
        for prefix in affected_prefixes:
            top_10 = db.query(Search).filter(Search.query.like(f"{prefix}%")).order_by(text("count * EXP(-0.02 * TIMESTAMPDIFF(HOUR, last_searched, NOW())) DESC")).limit(10).all()
            suggestions = [{"query": s.query, "count": s.count} for s in top_10]
            update_suggestions(prefix, suggestions)
            
        logger.info(f"[Batch] Flushed {len(current_updates)} unique queries to DB and Cache.")
    except Exception as e:
        logger.error(f"Error in batch flush logic: {e}")
        db.rollback()
    finally:
        db.close()

async def record_write_in_memory(query: str):
    global total_pending
    async with lock:
        pending_updates[query] += 1
        total_pending += 1
        
        if total_pending >= UPDATE_THRESHOLD:
            asyncio.create_task(flush_to_db_and_cache())
