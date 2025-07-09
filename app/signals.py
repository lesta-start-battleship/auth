import uuid
from blinker import Namespace
from errors import HttpError
from extensions import mail, confirm_code_redis
from flask_mail import Message
from smtplib import SMTPRecipientsRefused
from config import logger


registration_user_signal = Namespace().signal("registration-user")

def user_registered_handler(sender, **kwargs):
    """
    Обработчик сигнала регистрации пользователя
    """
    confirm_code = str(uuid.uuid4())
    username = kwargs.get("username")
    email = kwargs.get("email")

    confirm_code_redis.set(confirm_code, username)

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
        f"https://battleship-lesta-start.ru/auth/confirm_email/{confirm_code}\n\n"
        "С уважением,\n"
        "Команда игры Морской бой"
    )
    try:
        mail.send(msg)

    except SMTPRecipientsRefused as e:
        raise HttpError(400, "Некорректный email для подтверждения")

    except Exception as e:
        logger.error(f"Ошибка отправки письма: {e}")
        raise HttpError(500, "Ошибка отправки письма")
    