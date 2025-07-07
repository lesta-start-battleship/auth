from config import logger
from sqlalchemy.orm import Session
from kafka.producer import send_message_to_kafka
from kafka.services import (
    user_exists, get_user_currency, create_user_transaction_object,
    save_transaction
)
from database.models import CurrencyType, TransactionStatus


def handle_guild_war_declare(db: Session, msg: dict[str, str | int]) -> None:
    logger.info(
        f"[Обработчик] Обработка сообщения на топике: initiator_guild_wants_declare_war с данными: {msg}"
    )
    initiator_guild_id = msg["initiator_guild_id"]
    user_id = msg["initiator_owner_id"]
    correlation_id = msg["correlation_id"]
    transaction_id = f"guild:{correlation_id}"
    amount = 10

    if not user_exists(db, user_id):
        logger.warning(
            f"[Обработчик] Пользователь {user_id} не существует, транзакция пропускается"
        )
        send_message_to_kafka(
            topic="auth.guild_war.declare.response.guild",
            payload={
                "initiator_guild_id": initiator_guild_id,
                "initiator_owner_id": user_id,
                "correlation_id": correlation_id,
                "success": False,
            },
            target_service="guilds"
        )
        return None

    user_currency = get_user_currency(db, user_id)
    logger.info(
        f"[Обработчик] Получена информация о валюте пользователя {user_id}: {user_currency}"
    )
    transaction = create_user_transaction_object(
        transaction_id, user_id,  CurrencyType.GUILD_RAGE,
        amount,  TransactionStatus.PENDING
    )
    logger.info(f"[Обработчик] Создан объект транзакции: {transaction}")

    if not user_currency:
        transaction.status = TransactionStatus.DECLINED
        logger.warning(
            f"[Обработчик] Такой валюты у пользователя нет, транзакция отклонена"
        )
    else:
        available_amount = user_currency.guild_rage
        logger.info(
            f"[Обработчик] Доступный баланс по guild_rage: {available_amount}"
        )
        if available_amount >= amount:
            user_currency.guild_rage -= amount
            transaction.status = TransactionStatus.RESERVED
            logger.info(
                f"[Обработчик] Успешно зарезервировано {amount} guild_rage для пользователя {user_id}"
            )
        else:
            transaction.status = TransactionStatus.DECLINED
            logger.warning(
                f"[Обработчик] Недостаточно средств: требуется {amount}, доступно {available_amount}"
            )

    logger.info(
        f"[Обработчик] Сохранение транзакции в базу данных со статусом {transaction.status}"
    )
    save_transaction(db, transaction)
    logger.info(f"[Обработчик] Транзакция {transaction_id} успешно сохранена")
    logger.info("[Обработчик] Отправка ответа в Kafka...")
    send_message_to_kafka(
        topic="auth.guild_war.declare.response.guild",
        payload={
            "initiator_guild_id": initiator_guild_id,
            "initiator_owner_id": user_id,
            "correlation_id": correlation_id,
            "success": transaction.status == TransactionStatus.RESERVED,
        },
        target_service="guilds"
    )
