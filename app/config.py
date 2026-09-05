import os

from dotenv import load_dotenv

# Load .env into the environment before any value is read below.
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
# A local Redis runs without auth, so an unset/empty password means "no AUTH".
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

NUM_CLUSTERS = int(os.getenv("NUM_CLUSTERS", "49"))
NUM_LISTINGS_EACH = int(os.getenv("NUM_LISTINGS_EACH", "3"))
EPSILON = float(os.getenv("EPSILON", "0.3"))
