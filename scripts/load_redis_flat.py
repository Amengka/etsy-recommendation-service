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

# 数据批量写入
with open(DATA_DIR / "listingNames.txt", "r") as file:
    listingNames = file.read().split("\n")


for i, name in enumerate(listingNames): 
    filePath = DATA_DIR / "listings" / name
    category = name.split(".")[0]
    with open(filePath, "r") as file: 
        listings = file.read().split("\n")
        for listing in listings: 
            key = listing
            value = category
            client.set(key, value)

print("Data imported successfully.")