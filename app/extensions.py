import redis
import os
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

from config import CACHE_REDIS_HOST, CACHE_REDIS_PORT

oauth = OAuth()
mail = Mail()

jwt_redis_blocklist = redis.StrictRedis(
    host=CACHE_REDIS_HOST,
    port=CACHE_REDIS_PORT,
    db=0,
    decode_responses=True
)
device_login_redis = redis.StrictRedis(
    host=CACHE_REDIS_HOST,
    port=CACHE_REDIS_PORT,
    db=1,
    decode_responses=True
)

confirm_code_redis = redis.StrictRedis(
    host=CACHE_REDIS_HOST,
    port=CACHE_REDIS_PORT,
    db=2,
    decode_responses=True
)
