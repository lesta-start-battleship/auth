from flask_restx import Namespace

auth_ns = Namespace(
    "Auth",
    description="User registration, authentication and authorization"
)