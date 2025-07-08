from sqlalchemy.orm import Session

from database.models import (
    UserBase, UserCurrency, UserTransaction, CurrencyType, TransactionStatus
)
from config import logger
from kafka.producer import send_message_to_kafka
from kafka.services import (
    user_exists, get_user_transaction, get_user_currency, process_compensation
)


def handle_balance_compensate(db: Session, msg: dict[str, str | int]) -> None:
    logger.info(
        f"[Обработчик] Обработка сообщения на топике: shop.balance.compensate.request.auth с данными: {msg}"
    )
    transaction_id = msg["transaction_id"]
    prefixed_transaction_id = f"shop:{transaction_id}"
    user_id = msg["user_id"]
    amount = msg["cost"]
    currency = CurrencyType(msg["currency_type"].lower())
    error_message = "null"

    if amount <= 0:
        logger.warning(
            f"[Обработчик] Недопустимая сумма: {amount} для транзакции {prefixed_transaction_id}"
        )
        send_message_to_kafka(
            topic="auth.balance.compensate.response.shop",
            payload={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "success": False,
                "error_message": "invalid_cost"
            },
            target_service="shop"
        )
        return None

    if not user_exists(db, user_id):
        logger.warning(
            f"[Обработчик] Пользователь {user_id} не существует, транзакция пропускается"
        )
        send_message_to_kafka(
            topic="auth.balance.compensate.response.shop",
            payload={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "success": False,
                "error_message": "user_not_found"
            },
            target_service="shop"
        )
        return None

    transaction = get_user_transaction(db, prefixed_transaction_id, user_id)
    if not transaction:
        logger.warning(
            f"[Обработчик] Транзакция {prefixed_transaction_id} не найдена для пользователя {user_id}"
        )
        send_message_to_kafka(
            topic="auth.balance.compensate.response.shop",
            payload={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "success": False,
                "error_message": "transaction_not_found"
            },
            target_service="shop"
        )
        return None

    logger.info(
        f"[Обработчик] Найдена транзакция {prefixed_transaction_id} со статусом {transaction.status}"
    )
    user_currency = get_user_currency(db, user_id)
    if not user_currency:
        logger.warning("[Обработчик] Такой валюты у пользователя нет")
        send_message_to_kafka(
            topic="auth.balance.compensate.response.shop",
            payload={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "success": False,
                "error_message": "invalid_currency"
            },
            target_service="shop"
        )
        return None

    logger.info(
        f"[Обработчик] Выполнение компенсации: добавление {amount} {currency.value} пользователю {user_id}"
    )
    process_compensation(db, user_currency, currency, amount, transaction)
    logger.info(
        f"[Обработчик] Компенсация завершена, статус транзакции обновлен на {transaction.status}"
    )

    if currency == CurrencyType.GOLD:
        logger.info("[Обработчик] Отправка события изменения GOLD")
        send_message_to_kafka(
            topic="prod.auth.fact.currency-change.1",
            payload={
                "user_id": user_id, "gold": getattr(user_currency, "gold")
            },
            target_service="scoreboard"
        )

    logger.info("[Обработчик] Отправка ответа в Kafka...")
    send_message_to_kafka(
        topic="auth.balance.compensate.response.shop",
        payload={
            "transaction_id": transaction_id,
            "user_id": user_id,
            "success": True,
            "error_message": error_message
        },
        target_service="shop"
    )
