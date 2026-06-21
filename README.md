# Distributed Search Typeahead System

A complete working implementation of a distributed prefix-based search autocomplete / typeahead system designed with horizontal scaling, consistent hashing, caching, and a deferred cache maintenance strategy.

## Architecture
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
Consistent Hash Ring (Virtual Nodes)
  |
  +------------+------------+
  |            |            |
  v            v            v
Redis1       Redis2       Redis3
  |
  v
MySQL
```

## Setup Instructions
1. **Ensure Docker and Docker Compose are installed.**
2. **Start the distributed environment:**
   ```bash
   docker compose up --build
   ```
   *Note: This will spin up MySQL, 3 Redis nodes, 3 FastAPI application instances, and an Nginx reverse proxy.*

3. **Access the application:**
   Open a browser and navigate to [http://localhost:8000](http://localhost:8000). The frontend application is served natively through the API nodes and reverse proxied by Nginx.

## Dataset Loading Instructions
To populate the backend DB and initially warm up the Redis cache using consistent hashing rules, execute the dataset loader. Note that the application containers should be fully started first:

```bash
# Wait for mysql and API nodes to be ready, then run the load script from an app container
docker compose exec app1 python /code/scripts/load_dataset.py /code/dataset.csv
```

Alternatively, you could run it directly from your host if dependencies are installed:
```bash
python scripts/load_dataset.py dataset.csv
```

## API Documentation
- **GET /suggest?q=\<prefix\>** : Fetches up to 10 suggestions from the Redis cache using consistent hashing. Fallbacks to DB on Cache Miss.
- **POST /search** : Body: `{"query": "searching text"}`. Registers a search. Updates MySQL simultaneously, delays updating Redis to limit performance issues on inserts.
- **GET /trending** : Returns the top 10 search queries globally.
- **GET /cache/debug?prefix=\<prefix\>** : Retrieves diagnostics about how the suggestion for the prefix resolves on the Consistent Hash Ring (Hit/Miss, Responsible Node, Hash ID).
- **GET /metrics** : Tracks application instance metrics (Hits, Misses, Avg Latency, DB Reads/Writes).

## Consistent Hashing
The `HashRing` module incorporates a custom Consistent Hashing layer configured without external cluster plugins. It divides the hashing keyspace amongst virtual nodes (`node:0` through `node:99`) for 3 physical cache targets (`redis1`, `redis2`, `redis3`), assuring an even distribution of prefixes and robustness when cluster sizes change. It uses an MD5 hash function internally, resolving mapping to a standardized integer ring.

## Cache Design & Update Strategy
We maintain explicit cache control over Redis keys.
- **Format:** `suggest:<prefix>` containing a JSON serialized array of up to 10 sorted suggestions.
- **Consistency Model:** Database values overwrite and remain correct indefinitely. To counter expensive cache trimming per individual `POST /search`, we store tracking metrics inside an in-memory queue. Once 1000 searches are registered globally for a specific keyword within an instance, an asynchronous background task forces a Redis cache override for matching prefixes ensuring "eventual consistency."

## Query Recency (Time Decay)
The system utilizes an exponential time-decay calculation natively inside MySQL to elevate trending or recently searched queries above older data structurally. Using a specialized formula inside the SQL sorting logic (`count * EXP(-0.02 * TIMESTAMPDIFF(HOUR, last_searched, NOW()))`), the API inherently down-ranks queries proportional to the elapsed time since their last interaction. This yields an extremely realistic autocomplete engine without introducing overhead during high-speed cache checks.

## Tradeoffs and Limitations
- **Memory Consumption:** Storing all combinations of prefixes individually inside Redis uses significant memory. We have deliberately elected speed over memory consumption here to simulate high-throughput Typeahead designs.
- **In-Memory Tracking:** The deferred cache updating mechanism tracks incremental updates strictly within local App instance memory. In a distributed environment without IPC (Inter-Process Communication), metrics are partitioned across app instances meaning delay threshold evaluations aren't perfectly synchronized globally.
