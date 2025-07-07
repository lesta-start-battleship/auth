import uuid
from blinker import Namespace
from extensions import mail, confirm_code_redis
from flask_mail import Message

registration_user_signal = Namespace().signal("registration-user")

def user_registered_handler(sender, **kwargs):
    """
    Обработчик сигнала регистрации пользователя
    """
    confirm_code = str(uuid.uuid4())
    username = kwargs.get("username")
    email = kwargs.get("email")

    confirm_code_redis.set(confirm_code, username, ex=60*5)

    msg = Message(
        "Подтверждение почты при регистрации",
        recipients=[email]
    )
    msg.body = (
        f"Здравствуйте, {username}!\n\n"
        "Спасибо за регистрацию.\n"
        "Чтобы активировать вашу учетную запись, "
        "пожалуйста, подтвердите свой адрес электронной почты, "
        "перейдя по следующей ссылке:\n\n"
        f"http://127.0.0.1/api/v1/auth/confirm_email/{confirm_code}\n\n"
        "С уважением,\n"
        "Команда игры Морской бой"
    )
    mail.send(msg)
    