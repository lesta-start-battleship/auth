from config import logger
from sqlalchemy.orm import Session
from kafka.services import (
    user_exists, get_user_currency, get_user_transaction, process_compensation
)
from database.models import CurrencyType


def handle_guild_war_compensate(db: Session, msg: dict[str, str | int]) -> None:
    logger.info(
        f"[Обработчик] Обработка сообщения на топике: guild_war_canceled_declined_expired с данными: {msg}"
    )
    status = msg.get("status")

    if status not in {"declined", "canceled", "expired"}:
        logger.info(f"[Обработчик] Статус '{status}' не требует компенсации")
        return None

    user_id = msg["initiator_owner_id"]
    correlation_id = msg["correlation_id"]
    transaction_id = f"guild:{correlation_id}"
    amount = 10
    currency = CurrencyType.GUILD_RAGE

    if not user_exists(db, user_id):
        logger.warning(
            f"[Обработчик] Пользователь {user_id} не существует, транзакция пропускается"
        )
        return None

    transaction = get_user_transaction(db, transaction_id, user_id)
    if not transaction:
        logger.warning(
            f"[Обработчик] Транзакция {transaction_id} не найдена для пользователя {user_id}"
        )
        return None

    user_currency = get_user_currency(db, user_id)
    if not user_currency:
        logger.warning("[Обработчик] Такой валюты у пользователя нет")
        return None

    logger.info(
        f"[Обработчик] Выполнение компенсации: добавление {amount} {currency.value} пользователю {user_id}"
    )
    process_compensation(db, user_currency, currency, amount, transaction)
    logger.info(
        f"[Обработчик] Компенсация завершена, статус транзакции обновлен на {transaction.status}"
    )
