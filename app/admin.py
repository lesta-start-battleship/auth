from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from database.models import UserBase, UserCurrency, UserTransaction


admin = Admin(name="Auth admin panel", template_mode="bootstrap4")


class UserBaseAdminView(ModelView):
    column_list = (
        "id",
        "username",
        "name",
        "surname",
        "email",
        "is_active",
        "role",
        "created_at",
        "currencies"
    )
    column_exclude_list = ["h_password"]
    column_searchable_list = ["username", "email"]
    column_filters = ["role", "is_active"]
    page_size = 20


class UserCurrencyAdminView(ModelView):
    column_list = (
        "user_id",
        "guild_rage",
        "gold",
        "created_at",
        "user"
    )


class UserTransactionAdminView(ModelView):
    column_list = (
        "transaction_id",
        "user_id",
        "currency_type",
        "amount",
        "status",
        "created_at",
        "user"
    )
