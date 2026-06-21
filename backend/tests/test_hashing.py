from app.hashing.hash_ring import HashRing

def test_hash_ring_node_addition():
    nodes = ["redis1", "redis2", "redis3"]
    ring = HashRing(nodes=nodes, replicas=100)
    
    # Verify mapping is created properly
    assert len(ring.ring) == 300
    assert len(ring.sorted_keys) == 300

def test_hash_ring_consistency():
    nodes = ["redis1", "redis2", "redis3"]
    ring = HashRing(nodes=nodes, replicas=100)
    
    node1, hash1 = ring.get_node_with_hash("test-prefix-1")
    node2, hash2 = ring.get_node_with_hash("test-prefix-1")
    
    # Must explicitly route to same node if cluster isn't mutated
    assert node1 == node2
    assert hash1 == hash2

def test_hash_ring_node_removal():
    nodes = ["redis1", "redis2", "redis3"]
    ring = HashRing(nodes=nodes, replicas=100)
    
    node1, _ = ring.get_node_with_hash("test-prefix-2")
    assert node1 in nodes
    
    # Drop node and test redistribution
    ring.remove_node(node1)
    node_new, _ = ring.get_node_with_hash("test-prefix-2")
    
    assert node_new != node1
    assert node_new in nodes
    assert len(ring.ring) == 200
