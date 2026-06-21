import json
from .redis_client import redis_clients
from ..hashing.hash_ring import HashRing

nodes = list(redis_clients.keys())
hash_ring = HashRing(nodes=nodes, replicas=100)

def get_node_for_prefix(prefix: str):
    cache_key = f"suggest:{prefix}"
    node_name, hash_val = hash_ring.get_node_with_hash(cache_key)
    return node_name, redis_clients.get(node_name), hash_val

def get_suggestions(prefix: str):
    node_name, client, hash_val = get_node_for_prefix(prefix)
    if not client:
        return None, node_name, False, hash_val
    
    cache_key = f"suggest:{prefix}"
    res = client.get(cache_key)
    if res:
        return json.loads(res), node_name, True, hash_val
    return None, node_name, False, hash_val

def update_suggestions(prefix: str, suggestions: list):
    node_name, client, hash_val = get_node_for_prefix(prefix)
    if not client:
        return
    cache_key = f"suggest:{prefix}"
    client.set(cache_key, json.dumps(suggestions))

