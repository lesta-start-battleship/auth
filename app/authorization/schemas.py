from flask_restx import fields

from authorization.namespace import auth_ns


error_response = auth_ns.model("Error", {
    "error": fields.String(description="Error message"),
})

user_reg_request = auth_ns.model(
    "UserRegRequest", {
        "username": fields.String(required=True, write_only=True),
        "email": fields.String(
            required=True,
            write_only=True,
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        ),
        "password": fields.String(
            required=True,
            write_only=True,
            pattern=r"(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z]{8,}$"
        ),
        "name": fields.String,
        "surname": fields.String,

    }
)

user_reg_response = auth_ns.model(
    "UserRegResponse", {
        "access_token": fields.String,
        "refresh_token": fields.String,
    }
)

user_login_request = auth_ns.model(
    "UserLoginRequest", {
        "username": fields.String(required=True),
        "password": fields.String(required=True),
    }
)

user_login_response = auth_ns.model(
    "UserLoginResponse", {
        "access_token": fields.String,
        "refresh_token": fields.String,
    }
)


