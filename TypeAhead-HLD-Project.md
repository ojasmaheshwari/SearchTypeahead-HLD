# Build a Distributed Search Typeahead System (Python)

## Goal

Build a complete working implementation of a distributed search typeahead system similar to the suggestion feature used by search engines and e-commerce platforms.

The project should focus on demonstrating backend system-design concepts including:

* Prefix-based search suggestions
* Distributed caching
* Consistent hashing
* Horizontal scaling
* Cache maintenance
* Dataset ingestion
* Performance monitoring

The implementation must be fully containerized using Docker Compose and easy to run locally.

---

# Technology Stack

Use the following technologies:

* Python 3.12
* FastAPI for backend services
* MySQL for persistent storage
* Redis for distributed cache nodes
* Nginx as load balancer
* HTML/CSS/Vanilla JavaScript frontend
* Docker Compose for orchestration

Do not use external cloud services.

---

# Functional Requirements

## Suggest API

Endpoint:

```http
GET /suggest?q=<prefix>
```

Behavior:

* Return at most 10 suggestions.
* Suggestions must begin with the provided prefix.
* Suggestions must be sorted by search count descending.
* Matching should be case-insensitive.
* Handle empty input gracefully.
* Handle missing query parameter gracefully.
* Handle prefixes with no matches gracefully.

Example response:

```json
{
  "suggestions": [
    {
      "query": "iphone",
      "count": 100000
    },
    {
      "query": "iphone 15",
      "count": 85000
    }
  ]
}
```

---

## Search API

Endpoint:

```http
POST /search
```

Request:

```json
{
  "query": "iphone charger"
}
```

Response:

```json
{
  "message": "Searched"
}
```

Behavior:

* Return immediately after processing.
* Existing queries should have their count incremented.
* New queries should be inserted with count = 1.
* Updates must eventually appear in suggestions.

---

## Trending Searches API

Endpoint:

```http
GET /trending
```

Behavior:

* Return top 10 searches globally.
* Sort by overall search count.
* No recency ranking is required.

Example:

```json
[
  {
    "query": "iphone",
    "count": 100000
  }
]
```

---

## Cache Debug API

Endpoint:

```http
GET /cache/debug?prefix=<prefix>
```

Example response:

```json
{
  "prefix": "iph",
  "cache_node": "redis-node-2",
  "cache_hit": true,
  "hash": 1234567
}
```

Purpose:

* Demonstrate consistent hashing.
* Demonstrate cache routing.
* Show cache hit/miss information.

---

# Architecture

Implement the following architecture:

```text
Client
  |
  v
Nginx Load Balancer
  |
  +------------+------------+
  |            |            |
  v            v            v
App1         App2         App3
  |
  v
Consistent Hash Ring
  |
  +------------+------------+
  |            |            |
  v            v            v
Redis1       Redis2       Redis3
  |
  v
MySQL
```

---

# Load Balancer Requirements

Use Nginx.

Implement simple round-robin routing between:

* App1
* App2
* App3

Requirements:

* No sticky sessions
* No application-level sharding
* Requests can be distributed evenly across application servers

---

# Database Design

Create the following schema:

```sql
CREATE TABLE searches (
    query VARCHAR(255) PRIMARY KEY,
    count BIGINT NOT NULL
);
```

Add useful indexes if necessary.

---

# Dataset Loader

Provide a separate initialization script.

Input format:

```csv
query,count
iphone,100000
iphone 15,85000
iphone charger,60000
```

The loader must:

1. Read the CSV.
2. Insert all records into MySQL.
3. Generate prefix cache entries.
4. Populate the Redis cluster.
5. Build all required cache structures.

Example usage:

```bash
python scripts/load_dataset.py dataset.csv
```

This script should be runnable independently of the main application.

---

# Redis Cache Design

Cache suggestion results by prefix.

Example:

Key:

```text
suggest:iph
```

Value:

```json
[
  {"query":"iphone","count":100000},
  {"query":"iphone 15","count":85000}
]
```

Requirements:

* Store only the top 10 suggestions per prefix.
* No Redis TTL.
* No time-based cache expiration.
* Cache entries are maintained explicitly by the application.

The cache should serve suggestion requests before falling back to MySQL.

---

# Consistent Hashing

Implement a custom consistent hashing layer.

Do NOT use Redis Cluster.

Implement:

* Hash ring
* Virtual nodes
* Node lookup

Cache key format:

```text
suggest:<prefix>
```

Routing example:

```python
node = hash_ring.get_node(cache_key)
```

Requirements:

* Demonstrate distribution across 3 Redis nodes.
* Log routing decisions.
* Show routing through the debug endpoint.
* Use prefix cache keys as the hashing input.

Example:

```text
suggest:iph
        |
        v
hash_ring.get_node(...)
        |
        v
Redis2
```

---

# Suggestion Flow

When GET /suggest is called:

1. Normalize the prefix.
2. Generate cache key:

```text
suggest:<prefix>
```

3. Use consistent hashing to locate the Redis node.
4. Query Redis.

If cache hit:

* Return cached results.

If cache miss:

* Query MySQL.
* Retrieve top 10 matching queries ordered by count descending.
* Store result in the responsible Redis node.
* Return response.

---

# Search Count Update Strategy

Use synchronous database writes and delayed cache updates.

When POST /search is called:

1. Update MySQL immediately.
2. Return success response.
3. Increment an in-memory counter tracking searches since the last cache update.

Example:

```python
{
    "iphone": 352,
    "java tutorial": 87
}
```

Every search increments the corresponding counter.

When a query accumulates 1000 additional searches:

```python
pending_updates["iphone"] >= 1000
```

Then:

1. Recompute affected cache entries.
2. Update Redis.
3. Reset the counter.

Example:

```python
pending_updates["iphone"] = 0
```

This reduces expensive cache maintenance operations while keeping MySQL fully up-to-date.

---

# Cache Consistency Model

The system uses:

* Immediate database consistency
* Delayed cache consistency

Flow:

```text
POST /search
      |
      v
Update MySQL
      |
      v
Increment pending_updates counter
      |
      v
1000 additional searches
      |
      v
Update Redis cache entries
```

Tradeoff:

* Database is always correct.
* Cache may lag behind by up to 999 searches for a query.
* This is acceptable for the assignment because perfect real-time consistency is not required.

---

# Prefix Update Logic

Implement utility:

```python
update_prefixes(query)
```

Example:

Input:

```text
iphone
```

Generated prefixes:

```text
i
ip
iph
ipho
iphon
iphone
```

For each prefix:

1. Determine responsible Redis node via consistent hashing.
2. Fetch current cached top-10 list.
3. Compare updated count.
4. Insert/update ranking if necessary.
5. Trim list to top 10.
6. Save back to Redis.

---

# Frontend Requirements

Use:

* HTML
* CSS
* Vanilla JavaScript

Do not use React, Vue, Angular, or any frontend framework.

---

## Search Box

Requirements:

* Typing should trigger suggestions.
* Implement debounce.

Debounce interval:

```text
300 ms
```

Avoid unnecessary API requests.

---

## Suggestion Dropdown

Display:

* Query text
* Count

Maximum:

```text
10 suggestions
```

Support:

* Up arrow navigation
* Down arrow navigation
* Enter key selection

---

## Search Submission

Support:

* Search button
* Enter key

Display:

```text
Searched
```

after a successful request.

---

## Trending Section

Display:

* Top 10 searches globally

Use:

```http
GET /trending
```

---

## Loading and Error States

Implement:

* Loading indicators
* API error messages
* Empty result states

---

# Logging

Log:

* Cache hits
* Cache misses
* Redis node selected
* Hash values
* Database reads
* Database writes
* Prefix rebuild operations
* Cache update events

Example:

```text
[Cache] suggest:iph -> Redis2
[Cache] HIT

[Cache] suggest:jav -> Redis1
[Cache] MISS
```

---

# Metrics Endpoint

Create:

```http
GET /metrics
```

Example response:

```json
{
  "cache_hits": 100,
  "cache_misses": 20,
  "cache_hit_rate": 0.83,
  "db_reads": 50,
  "db_writes": 1000,
  "average_latency_ms": 12
}
```

Track metrics in memory.

---

# Docker Requirements

Create the following services:

* nginx
* app1
* app2
* app3
* mysql
* redis1
* redis2
* redis3

Provide a complete Docker Compose configuration.

The entire system must start with:

```bash
docker compose up --build
```

---

# README Requirements

Include:

* Architecture diagram
* Setup instructions
* Dataset loading instructions
* API documentation
* Consistent hashing explanation
* Cache design explanation
* Cache update strategy explanation
* Tradeoffs and limitations
* Performance metrics
* Example requests and responses

---

# Suggested Project Structure

```text
project/
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── cache/
│   │   ├── hashing/
│   │   ├── db/
│   │   ├── services/
│   │   ├── metrics/
│   │   └── models/
│   │
│   └── Dockerfile
│
├── scripts/
│   └── load_dataset.py
│
├── docker-compose.yml
│
├── nginx/
│   └── nginx.conf
│
└── README.md
```

Generate complete, runnable, production-quality code for all files, including:

* FastAPI backend
* MySQL integration
* Redis integration
* Consistent hashing implementation
* Virtual nodes
* Dataset ingestion script
* Prefix generation logic
* Cache update logic
* Metrics collection
* Logging
* Nginx configuration
* Docker configuration
* Frontend implementation
* README documentation

The final output should be a complete project that can be cloned, built with Docker Compose, loaded with a CSV dataset, and demonstrated locally.
