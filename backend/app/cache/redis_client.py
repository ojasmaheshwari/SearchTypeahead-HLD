import os
import redis

# Defaults to localhost for local run without compose; override via env.
REDIS_NODES_ENV = os.getenv("REDIS_NODES", "redis1:6379,redis2:6379,redis3:6379")

def init_redis_clients():
    clients = {}
    nodes = REDIS_NODES_ENV.split(",")
    for node in nodes:
        host, port = node.split(":")
        # Provide default local mappings if testing outside docker compose
        if host.startswith("redis"):
            host_mapped = host
        else:
            host_mapped = host
            
        clients[host] = redis.Redis(host=host_mapped, port=int(port), decode_responses=True)
    return clients

redis_clients = init_redis_clients()
