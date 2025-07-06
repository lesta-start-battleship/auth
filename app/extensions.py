import redis
import os
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth


oauth = OAuth()
mail = Mail()

jwt_redis_blocklist = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=os.getenv("REDIS_PORT", 6379),
    db=0,
    decode_responses=True
)

confirm_code_redis = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=os.getenv("REDIS_PORT", 6379),
    db=2,
    decode_responses=True
)
