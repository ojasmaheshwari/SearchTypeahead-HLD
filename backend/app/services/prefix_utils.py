def get_prefixes(query: str):
    query = query.strip().lower()
    prefixes = []
    for i in range(1, len(query) + 1):
        prefixes.append(query[:i])
    return prefixes
