from flask_restx import fields
from app.users.namespace import user_ns


error_response = user_ns.model(
    "Error", {
        "error": fields.String(description="Error message"),
    }
)

get_user_response = user_ns.model(
    "GetUserResponse", {
        "id": fields.Integer,
        "email": fields.String,
        "username": fields.String,
        "role": fields.String,
        "currency": fields.Nested(
            {
                "gold": fields.Integer,
                "silver": fields.Integer
            }
        )
    }
)

get_users_list_request = user_ns.model(
    "GetUserListRequest", {
        "user_ids": fields.List(fields.Integer(required=True), required=True)
    }
)

get_users_list_response = user_ns.model(
    "GetUserListResponse", {
        "users": fields.List(fields.Nested(get_user_response))
    }
)

update_user_request = user_ns.model(
    "UpdateUserRequest", {
        "email": fields.String,
        "username": fields.String,
        "password": fields.String(write_only=True),
        "role": fields.String
    }
)

update_user_response = user_ns.model(
    "UpdateUserResponse", {
        "id": fields.Integer,
        "email": fields.String,
        "username": fields.String,
        "role": fields.String
    }
)