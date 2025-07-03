import redis
import os
from authlib.integrations.flask_client import OAuth


oauth = OAuth()

jwt_redis_blocklist = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=os.getenv("REDIS_PORT", 6379),
    db=0,
    decode_responses=True
)
