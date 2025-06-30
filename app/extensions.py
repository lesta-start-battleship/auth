import redis
from authlib.integrations.flask_client import OAuth

oauth = OAuth()

jwt_redis_blocklist = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)
