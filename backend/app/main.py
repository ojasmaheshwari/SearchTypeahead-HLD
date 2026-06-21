import os
import time
import logging
from typing import Optional
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from .db.database import get_db, engine, Base
from .db.models import Search
from .cache.cache_manager import get_suggestions, update_suggestions
from .services.cache_updater import increment_pending_updates
from .metrics.metrics import metrics
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Apply tables
Base.metadata.create_all(bind=engine)

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE searches ADD COLUMN last_searched DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;"))
except Exception as e:
    pass

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    metrics.record_latency(process_time * 1000)
    return response

@app.get("/suggest")
def suggest(q: Optional[str] = None, db: Session = Depends(get_db)):
    if not q:
        return JSONResponse({"suggestions": []})
    
    q = q.strip().lower()
    if not q:
        return JSONResponse({"suggestions": []})
        
    cache_res, node_name, is_hit, hash_val = get_suggestions(q)
    
    if is_hit:
        logger.info(f"[Cache] suggest:{q} -> {node_name}")
        logger.info(f"[Cache] HIT")
        metrics.record_cache_hit()
        return JSONResponse({"suggestions": cache_res})
    
    logger.info(f"[Cache] suggest:{q} -> {node_name}")
    logger.info(f"[Cache] MISS")
    metrics.record_cache_miss()
    
    metrics.record_db_read()
    results = db.query(Search).filter(Search.query.like(f"{q}%")).order_by(text("count * EXP(-0.02 * TIMESTAMPDIFF(HOUR, last_searched, NOW())) DESC")).limit(10).all()
    suggestions = [{"query": res.query, "count": res.count} for res in results]
    
    update_suggestions(q, suggestions)
    
    return JSONResponse({"suggestions": suggestions})

@app.post("/search")
def search(req: SearchRequest, db: Session = Depends(get_db)):
    q = req.query.strip().lower()
    if not q:
        return JSONResponse({"message": "Empty query"}, status_code=400)
        
    metrics.record_db_write()
    search_record = db.query(Search).filter(Search.query == q).first()
    if search_record:
        search_record.count += 1
    else:
        search_record = Search(query=q, count=1)
        db.add(search_record)
    
    db.commit()
    
    increment_pending_updates(q)
    
    return JSONResponse({"message": "Searched"})

@app.get("/trending")
def trending(db: Session = Depends(get_db)):
    metrics.record_db_read()
    results = db.query(Search).order_by(text("count * EXP(-0.02 * TIMESTAMPDIFF(HOUR, last_searched, NOW())) DESC")).limit(10).all()
    out = [{"query": r.query, "count": r.count} for r in results]
    return JSONResponse(out)

@app.get("/cache/debug")
def cache_debug(prefix: str):
    cache_res, node_name, is_hit, hash_val = get_suggestions(prefix)
    return JSONResponse({
        "prefix": prefix,
        "cache_node": node_name,
        "cache_hit": is_hit,
        "hash": hash_val
    })

@app.get("/metrics")
def get_metrics_endpoint():
    return JSONResponse(metrics.get_metrics())

frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if not os.path.exists(frontend_path):
    frontend_path = "/code/frontend"
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
