import redis
import json
import random
import logging
from typing import List, Optional

from fastapi import HTTPException

from . import config

# Configure logging with timestamp and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Redis client from environment configuration (see .env.example)
redis_client = redis.StrictRedis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    password=config.REDIS_PASSWORD,
    decode_responses=True
)

def get_user_interaction_history(user_id: int) -> List[int]:
    """
    Retrieve the user's cluster interaction history from Redis.
    
    Args:
        user_id: The unique identifier for the user
        
    Returns:
        List of cluster IDs the user has interacted with
    """
    history_key = f"user:{user_id}:interaction_history"
    logging.info(f"Fetching interaction history for user {user_id}")
    
    user_history = redis_client.get(history_key)
    if not user_history:
        logging.warning(f"No interaction history found for user {user_id}")
        return []
    
    try:
        cleaned_history = user_history.strip().replace('\xa0', ' ')
        parsed_history = json.loads(cleaned_history)
        cluster_ids = parsed_history.get('cluster_history', [])
        
        logging.info(f"Successfully retrieved {len(cluster_ids)} historical clusters for user {user_id}")
        return cluster_ids
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse interaction history for user {user_id}: {e}")
        return []

def update_cluster_weights(user_id: int, cluster_ids: List[int]) -> None:
    """
    Update weights for clusters based on user interactions.
    Implements a simple incrementing counter for each cluster interaction.
    
    Args:
        user_id: The unique identifier for the user
        cluster_ids: List of cluster IDs to update weights for
    """
    weights_key = f"user:{user_id}:cluster_weights"
    
    if not cluster_ids:
        logging.warning(f"No clusters to update weights for user {user_id}")
        return
        
    for cluster_id in cluster_ids:
        redis_client.zincrby(weights_key, 1, f"cluster:{cluster_id}")
    
    logging.info(f"Updated weights for user {user_id}, clusters: {cluster_ids}")

def find_fav_clusters(user_id: int, top_n: int = 10) -> List[int]:
    """
    Identify user's favorite clusters based on interaction weights.
    
    Args:
        user_id: The unique identifier for the user
        top_n: Number of top clusters to return
        
    Returns:
        List of top cluster IDs
    """
    weights_key = f"user:{user_id}:cluster_weights"
    weights = redis_client.zrange(weights_key, 0, -1, withscores=True, desc=True)
    
    top_clusters = [int(cluster_id.split(':')[1]) for cluster_id, score in weights[:top_n]]
    logging.info(f"Found {len(top_clusters)} favorite clusters for user {user_id}")
    
    return top_clusters

def recommend_cluster(user_id: int, top_clusters: List[int], epsilon: float = config.EPSILON) -> int:
    """
    Select a cluster using epsilon-greedy strategy.
    
    Args:
        user_id: The unique identifier for the user
        top_clusters: List of user's favorite clusters
        epsilon: Exploration probability
        
    Returns:
        Selected cluster ID
    """
    if not top_clusters:
        selected = random.randint(0, config.NUM_CLUSTERS - 1)
        logging.info(f"No favorite clusters for user {user_id}, randomly selected cluster {selected}")
        return selected
        
    if random.random() < epsilon:  # Exploration
        selected = random.randint(0, config.NUM_CLUSTERS - 1)
        logging.info(f"Exploration: Selected random cluster {selected} for user {user_id}")
    else:  # Exploitation
        selected = random.choice(top_clusters)
        logging.info(f"Exploitation: Selected favorite cluster {selected} for user {user_id}")
    
    return selected

def sample_cluster(cluster_id: int, num_samples: int) -> List[str]:
    """
    Sample listings from a specific cluster.
    
    Args:
        cluster_id: The cluster to sample from
        num_samples: Number of listings to sample
        
    Returns:
        List of sampled listing IDs
    """
    cluster_key = f"cluster:{cluster_id}"
    listings = redis_client.lrange(cluster_key, 0, -1)
    
    if not listings:
        logging.warning(f"No listings found in cluster {cluster_id}")
        return []
    
    samples = random.sample(listings, min(num_samples, len(listings)))
    logging.info(f"Sampled {len(samples)} listings from cluster {cluster_id}")
    return samples

async def get_top_recommendations(
    user_id: int, 
    num_clusters: int = 3, 
    num_listings_per_cluster: int = 3
) -> dict:
    """
    Generate personalized recommendations for a user.
    
    Args:
        user_id: The unique identifier for the user
        num_clusters: Number of clusters to recommend from
        num_listings_per_cluster: Number of listings to recommend per cluster
        
    Returns:
        Dictionary containing user_id and recommended listing IDs
    """
    try:
        logging.info(f"Generating recommendations for user {user_id}")
        
        clicked_clusters = get_user_interaction_history(user_id)
        update_cluster_weights(user_id, clicked_clusters)
        top_clusters = find_fav_clusters(user_id)
        
        recommended_listings = []
        for i in range(num_clusters):
            cluster = recommend_cluster(user_id, top_clusters)
            listings = sample_cluster(cluster, num_listings_per_cluster)
            recommended_listings.extend(listings)
        
        logging.info(f"Successfully generated {len(recommended_listings)} recommendations for user {user_id}")
        return {"user_id": user_id, "recommendations": recommended_listings}
        
    except Exception as e:
        logging.error(f"Failed to generate recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
