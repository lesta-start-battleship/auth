from blinker import Namespace
from kafka.kafka import send_kafka


registration_user_signal = Namespace().signal("registration-user")
change_username_signal = Namespace().signal("change-username")


def user_registered_handler(sender, **kwargs):
    """
    Обработчик сигнала регистрации пользователя
    """
    user_id = kwargs.get("user_id")

    send_kafka(
        "inventory-new-user",
        {
            "message": "New user registered",
            "user_id": user_id
        }
    )


def change_username_handler(sender, **kwargs):
    """
    Обработчик сигнала изменения имени пользователя
    """
    user_id = kwargs.get("user_id")
    username = kwargs.get("username")

    send_kafka(
        "Какие-то топики кому нужно",
        {
            "message": "Username changed",
            "user_id": user_id,
            "username": username
        }
    )
