from app.services.prefix_utils import get_prefixes
from app.metrics.metrics import MetricsManager

def test_get_prefixes_standard():
    query = "apple"
    prefixes = get_prefixes(query)
    assert prefixes == ["a", "ap", "app", "appl", "apple"]

def test_get_prefixes_with_spaces_and_caps():
    query = " IPhoNe "
    prefixes = get_prefixes(query)
    assert prefixes == ["i", "ip", "iph", "ipho", "iphon", "iphone"]

def test_metrics_manager():
    metrics = MetricsManager()
    
    # Verify defaults
    assert metrics.get_metrics()["cache_hits"] == 0
    assert metrics.get_metrics()["cache_hit_rate"] == 0.0
    
    # Increment
    metrics.record_cache_hit()
    metrics.record_cache_miss()
    metrics.record_cache_miss()
    metrics.record_db_read()
    metrics.record_db_write()
    metrics.record_latency(50)
    metrics.record_latency(150)
    
    data = metrics.get_metrics()
    assert data["cache_hits"] == 1
    assert data["cache_misses"] == 2
    assert data["cache_hit_rate"] == 0.33  # 1 / 3
    assert data["db_reads"] == 1
    assert data["db_writes"] == 1
    assert data["average_latency_ms"] == 100.0  # 200 / 2
