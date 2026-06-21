class MetricsManager:
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.db_reads = 0
        self.db_writes = 0
        self.total_latency_ms = 0.0
        self.request_count = 0

    def record_cache_hit(self):
        self.cache_hits += 1

    def record_cache_miss(self):
        self.cache_misses += 1

    def record_db_read(self):
        self.db_reads += 1

    def record_db_write(self):
        self.db_writes += 1

    def record_latency(self, latency_ms: float):
        self.total_latency_ms += latency_ms
        self.request_count += 1

    def get_metrics(self):
        hit_rate = 0.0
        total_cache = self.cache_hits + self.cache_misses
        if total_cache > 0:
            hit_rate = self.cache_hits / total_cache
        
        avg_latency = 0.0
        if self.request_count > 0:
            avg_latency = self.total_latency_ms / self.request_count

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(hit_rate, 2),
            "db_reads": self.db_reads,
            "db_writes": self.db_writes,
            "average_latency_ms": round(avg_latency, 2)
        }

metrics = MetricsManager()
