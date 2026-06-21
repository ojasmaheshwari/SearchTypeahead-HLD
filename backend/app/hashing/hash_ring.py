import hashlib
import bisect

class HashRing:
    def __init__(self, nodes=None, replicas=100):
        self.replicas = replicas
        self.ring = dict()
        self.sorted_keys = []
        if nodes:
            for node in nodes:
                self.add_node(node)

    def _hash(self, key):
        # Taking md5 and parsing directly to integer provides a reliable and even distribution
        # Limiting to 64 bytes maybe not necessary, but returning standard int
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_node(self, node):
        for i in range(self.replicas):
            virtual_node_name = f"{node}:{i}"
            key = self._hash(virtual_node_name)
            self.ring[key] = node
            bisect.insort(self.sorted_keys, key)

    def remove_node(self, node):
        for i in range(self.replicas):
            virtual_node_name = f"{node}:{i}"
            key = self._hash(virtual_node_name)
            if key in self.ring:
                del self.ring[key]
                self.sorted_keys.remove(key)

    def get_node(self, string_key):
        if not self.ring:
            return None
        hash_val = self._hash(string_key)
        
        index = bisect.bisect_left(self.sorted_keys, hash_val)
        
        if index == len(self.sorted_keys):
            index = 0
            
        return self.ring[self.sorted_keys[index]]

    def get_node_with_hash(self, string_key):
        if not self.ring:
            return None, None
        hash_val = self._hash(string_key)
        
        index = bisect.bisect_left(self.sorted_keys, hash_val)
        
        if index == len(self.sorted_keys):
            index = 0
            
        return self.ring[self.sorted_keys[index]], str(hash_val)  # String to avoid JSON huge int issues
