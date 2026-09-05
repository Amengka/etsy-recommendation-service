import json
import os
from pathlib import Path

import redis
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# connect Redis (see .env.example)
client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD") or None,
    decode_responses=True,
)

pipeline = client.pipeline()

with open(DATA_DIR / "listingNames.txt", "r") as file:
    listingNames = file.read().split("\n")


for i, name in enumerate(listingNames): 
    filePath = DATA_DIR / "listings" / name
    category = name.split(".")[0]
    listings = list()
    with open(filePath, "r") as file: 
        data = file.read().split("\n")
        for listing in data: 
            # Reverse map(listing id -> cluser id)
            pipeline.hset("listing_to_cluster", listing, i)
            listings.append(listing)
    key = f"cluster:{i}"
    # Cluster (list)
    pipeline.rpush(key, *listings)


# User Interaction History
user_id = "user_12345"
cluster_id = 0

data = {
    "click_history": [
    {"listing_id": 1582998659, "timestamp": "2024-11-24T10:00:00Z"},
    {"listing_id": 1663229576, "timestamp": "2024-11-24T10:05:00Z"},
    {"listing_id": 1700023476, "timestamp": "2024-11-24T10:15:00Z"}
], 
    "view_history": [
    {"listing_id": 1700023473, "timestamp": "2024-11-24T09:50:00Z"},
    {"listing_id": 1663229575, "timestamp": "2024-11-24T09:55:00Z"},
    {"listing_id": 1582998660, "timestamp": "2024-11-24T09:57:00Z"},
    {"listing_id": 1582998659, "timestamp": "2024-11-24T10:00:00Z"},
    {"listing_id": 1663229576, "timestamp": "2024-11-24T10:05:00Z"},
    {"listing_id": 1700023476, "timestamp": "2024-11-24T10:15:00Z"}
]
}

key = f"user:{user_id}:interaction_history"
pipeline.set(key, json.dumps(data))

# User-specific cluster stats
value = {
    "clicks": 10, 
    "views": 50
}

key = f"user:{user_id}:cluster:{cluster_id}:interactions"
pipeline.set(key, json.dumps(value))

# User-specific cluster Cluster Weights

cluster_weights = {
    "cluster:0": 0.15,
    "cluster:1": 0.08
}

key = f"user:{user_id}:cluster_weights"

for cluster, weight in cluster_weights.items():
    pipeline.zadd(key, {cluster: weight})

pipeline.execute()
print("Data imported successfully.")