from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_suggest_no_query():
    res = client.get("/suggest")
    assert res.status_code == 200
    assert res.json() == {"suggestions": []}

def test_suggest_with_query():
    res = client.get("/suggest?q=test")
    assert res.status_code == 200
    data = res.json()
    assert "suggestions" in data
    assert type(data["suggestions"]) is list

def test_search_insert():
    res = client.post("/search", json={"query": "automated test query"})
    assert res.status_code == 200
    assert res.json() == {"message": "Searched"}

def test_search_empty():
    res = client.post("/search", json={"query": " "})
    assert res.status_code == 400
    assert res.json() == {"message": "Empty query"}

def test_trending():
    res = client.get("/trending")
    assert res.status_code == 200
    data = res.json()
    assert type(data) is list

def test_cache_debug():
    res = client.get("/cache/debug?prefix=auto")
    assert res.status_code == 200
    data = res.json()
    assert "cache_node" in data
    assert "cache_hit" in data
    assert "hash" in data

def test_metrics():
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "cache_hits" in data
    assert "cache_misses" in data

def test_search_update_increment():
    import uuid
    from app.db.database import SessionLocal
    from app.db.models import Search
    
    # Use a highly arbitrary random string to prevent database interference
    test_query = f"xjzhj_{uuid.uuid4().hex[:6]}"
    
    # 1. Trigger insertion
    client.post("/search", json={"query": test_query})
    
    db = SessionLocal()
    try:
        record1 = db.query(Search).filter(Search.query == test_query).first()
        assert record1 is not None
        assert record1.count == 1
        
        # 2. Trigger update (increment)
        client.post("/search", json={"query": test_query})
        
        db.commit() # Clear transaction state to bust REPEATABLE READ isolation
        record2 = db.query(Search).filter(Search.query == test_query).first()
        assert record2.count == 2
        
        # 3. Trigger again
        client.post("/search", json={"query": test_query})
        db.commit()
        record3 = db.query(Search).filter(Search.query == test_query).first()
        assert record3.count == 3
    finally:
        # Cleanup
        db.commit()
        db.query(Search).filter(Search.query == test_query).delete()
        db.commit()
        db.close()
