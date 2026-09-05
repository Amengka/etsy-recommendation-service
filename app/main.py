from fastapi import FastAPI

from . import config
from .recommender import get_top_recommendations

app = FastAPI(
    title="Etsy Recommendation Service",
    description="Prototype recommendation service balancing exploitation of a "
                "user's preferred clusters against exploration of new ones.",
)


@app.get("/")
async def root():
    return {"message": "Recommendation Service is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "redis_host": config.REDIS_HOST}


# Recommendation endpoint, implemented in recommender.py
app.get("/recommendations/{user_id}")(get_top_recommendations)
