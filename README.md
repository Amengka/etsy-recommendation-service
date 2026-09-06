# Etsy Recommendation Service

A prototype recommendation service that balances **exploitation** of a user's
preferred product clusters against **exploration** of unfamiliar ones, using an
epsilon-greedy strategy over listing clusters stored in Redis.

Built for CS6220 (Data Mining Techniques) at Northeastern University, in a
collaboration with Etsy staff engineers and scientists.

---

## Why

Most recommenders optimise for *relevance*: given what you bought before, show
more of the same. That works for a buyer who is close to checking out. It works
badly for a buyer who is browsing — looking for a gift, or just window shopping.
On a marketplace like Etsy, where the inventory is long-tail and idiosyncratic, a
purely relevance-driven feed under-serves both the browsing buyer and the niche
seller.

This service takes the opposite starting point: recommendations are **sampled**
from a distribution over clusters, and that distribution is shaped — but never
fully determined — by the user's interaction history.

## How it works

The 105,404 listing IDs in this repo are grouped into 49 clusters, one per Etsy
search query (`chair`, `keychain`, `yarn`, …). Serving a request is three steps:

1. **Read history** — fetch the clusters this user has previously interacted with.
2. **Update weights** — increment a per-user sorted set, one point per interaction.
3. **Sample** — for each of `num_clusters` slots, pick a cluster epsilon-greedily
   (with probability `EPSILON` pick uniformly at random; otherwise pick from the
   user's top-weighted clusters), then draw `num_listings_per_cluster` listings
   at random from it.

The exploration term is what keeps the feed from collapsing onto whatever the
user clicked first.

```
GET /recommendations/{user_id}
        │
        ├── user:{id}:interaction_history   (string, JSON)   → clusters seen
        ├── user:{id}:cluster_weights       (sorted set)     → ZINCRBY, then ZRANGE desc
        └── cluster:{n}                     (list)           → LRANGE + random.sample
```

## Redis data model

| Key | Type | Contents |
| --- | --- | --- |
| `cluster:{cluster_id}` | list | ~3,000 listing IDs for one search query |
| `listing_to_cluster` | hash | listing ID → cluster ID (reverse lookup; Redis has no efficient reverse scan over the lists above) |
| `user:{user_id}:interaction_history` | string (JSON) | the user's click/view history |
| `user:{user_id}:cluster_weights` | sorted set | `cluster:{n}` → interaction count, used to rank favourites |
| `user:{user_id}:cluster:{n}:interactions` | string (JSON) | per-cluster click/view counters |

## Quickstart

```bash
git clone https://github.com/Amengka/etsy-recommendation-service.git
cd etsy-recommendation-service
cp .env.example .env
```

**Run the service and Redis together:**

```bash
docker compose up --build       # API on http://localhost:8000
```

**Load the listing data into Redis** (once, from the host):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/load_redis.py    # ~105k listing IDs across 49 clusters
```

**Try it:**

```bash
curl localhost:8000/health
curl "localhost:8000/recommendations/42?num_clusters=3&num_listings_per_cluster=3"
```

```json
{
  "user_id": 42,
  "recommendations": ["1215795577", "1520350816", "1753531068", "..."]
}
```

Interactive API docs at <http://localhost:8000/docs>.

## Configuration

All settings come from the environment; see `.env.example`. Defaults target a
local Redis with no authentication.

| Variable | Default | Meaning |
| --- | --- | --- |
| `REDIS_HOST` | `localhost` | Redis hostname (`redis` inside Docker Compose) |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | *(empty)* | Leave empty for a local Redis without auth |
| `NUM_CLUSTERS` | `49` | Number of clusters available to sample from |
| `NUM_LISTINGS_EACH` | `3` | Default listings returned per cluster |
| `EPSILON` | `0.3` | Probability of exploring instead of exploiting |

## API

### `GET /recommendations/{user_id}`

| Parameter | Type | Default | |
| --- | --- | --- | --- |
| `user_id` | int | — | path parameter |
| `num_clusters` | int | 3 | how many clusters to draw from |
| `num_listings_per_cluster` | int | 3 | listings sampled per cluster |

Returns `{"user_id": int, "recommendations": [listing_id, ...]}`. Listing IDs
resolve to real pages at `https://www.etsy.com/listing/{listing_id}`.

### `GET /health`

Liveness check; also echoes the configured Redis host.

## Repository layout

```
app/
  main.py              FastAPI application and routes
  recommender.py       epsilon-greedy sampling logic
  config.py            environment-driven configuration
scripts/
  build_listing_index.py   data/raw/ → data/listingNames.txt
  extract_listing_ids.py   data/raw/ → data/listings/ (parses IDs out of the dumps)
  load_redis.py            data/listings/ → Redis (clusters + reverse index)
  load_redis_flat.py       simpler listing → category key/value load
data/
  raw/                 49 files, one per Etsy search query, as originally provided
  listings/            the same data reduced to bare newline-separated listing IDs
  listingNames.txt     the cluster ordering; index in this file = cluster ID
```

`data/listings/` is derived from `data/raw/` — running
`scripts/extract_listing_ids.py` reproduces it byte for byte.

## Data

The dataset was provided by the course instructor from real Etsy data: 49 search
queries, ~3,000 listing IDs each, 105,404 in total. It contains **only numeric
listing identifiers** — no user data, no seller data, no product content.

## Known limitations

This was a one-semester prototype; these are real gaps, not oversights hidden
behind the README:

- **`POST /update_clicks` is not implemented.** Interaction history has to be
  written to Redis directly. Weight updates currently happen as a side effect of
  reading recommendations, which conflates "was shown" with "was clicked".
- **The seeded demo user is inert.** `load_redis.py` writes
  `user:user_12345:interaction_history` in a `{click_history, view_history}`
  shape, but the recommender reads `user:{int}:interaction_history` and expects a
  `cluster_history` key. The two were never reconciled, so the seeded user falls
  through to the cold-start path.
- **No cold-start signal.** A user with no history gets uniformly random
  clusters; listing metadata (price, tags, popularity) is unused.
- **No evaluation.** No precision/recall or click-through measurement, and no
  comparison against a relevance-only baseline.
- **No test suite.**

## Project context

Course project for CS6220, Fall 2024, by Chieh-Han (Aaron) Chen, Wenhanfu Yang,
Ziting Wang, and Hsin-Yu (Joy) Guo. It was originally developed in a private
repository on Northeastern's GitHub Enterprise instance; this is a public copy so
the work can be read without an institutional account.

Ziting Wang's contribution was the Redis data model and the data ingestion
pipeline under `scripts/`.

## License

MIT — see [LICENSE](LICENSE).
