from functools import wraps

from app.database.database import session


def with_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with session() as db:
            try:
                return func(*args, session_db=db, **kwargs)
            finally:
                db.close()

    return wrapper
