from config import logger
from sqlalchemy.orm import Session
from database.models import (
    UserBase, UserCurrency, UserTransaction, CurrencyType, TransactionStatus
)
from kafka.producer import send_message_to_kafka
from kafka.services import (
    user_exists, get_user_currency, create_user_transaction_object,
    save_transaction
)


def handle_balance_reserve(db: Session, msg: dict[str, str | int]) -> None:
    logger.info(
        f"[Обработчик] Обработка сообщения на топике: shop.balance.reserve.request.auth с данными: {msg}"
    )
    transaction_id = msg["transaction_id"]
    user_id = msg["user_id"]
    amount = msg["cost"]
    currency = CurrencyType(msg["currency_type"].lower())
    error_message = "null"

    if amount <= 0:
        logger.warning(f"Недопустимая сумма: {amount} для транзакции {transaction_id}")
        send_message_to_kafka(
            topic="auth.balance.reserve.response.shop",
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
            topic="auth.balance.reserve.response.shop",
            payload={
                "transaction_id": transaction_id,
                "user_id": user_id,
                "success": False,
                "error_message": "user_not_found"
            },
            target_service="shop"
        )
        return None

    user_currency = get_user_currency(db, user_id)
    logger.info(
        f"[Обработчик] Получена информация о валюте пользователя {user_id}: {user_currency}"
    )
    transaction = create_user_transaction_object(
        f"shop:" + transaction_id, user_id, currency, amount, TransactionStatus.PENDING
    )
    logger.info(f"[Обработчик] Создан объект транзакции: {transaction}")

    if not user_currency:
        transaction.status = TransactionStatus.DECLINED
        error_message = "invalid_currency"
        logger.warning(
            f"[Обработчик] Такой валюты у пользователя нет, транзакция отклонена"
        )
    else:
        available_amount = getattr(user_currency, currency.value)
        logger.info(
            f"[Обработчик] Доступный баланс по {currency.value}: {available_amount}"
        )
        if available_amount >= amount:
            setattr(user_currency, currency.value, available_amount - amount)
            transaction.status = TransactionStatus.RESERVED
            logger.info(
                f"[Обработчик] Успешно зарезервировано {amount} {currency.value} для пользователя {user_id}"
            )
        else:
            transaction.status = TransactionStatus.DECLINED
            error_message = "insufficient_funds"
            logger.warning(
                f"[Обработчик] Недостаточно средств: требуется {amount}, доступно {available_amount}"
            )

    logger.info(
        f"[Обработчик] Сохранение транзакции в базу данных со статусом {transaction.status}"
    )
    save_transaction(db, transaction)
    logger.info(f"[Обработчик] Транзакция {transaction_id} успешно сохранена")

    if (
        currency == CurrencyType.GOLD and
        transaction.status == TransactionStatus.RESERVED
    ):
        logger.info(
            f"[Обработчик] Отправка события изменения GOLD"
        )
        send_message_to_kafka(
            topic="prod.auth.fact.currency-change.1",
            payload={
                "user_id": user_id, "gold": getattr(user_currency, "gold")
            },
            target_service="scoreboard"
        )

    logger.info("[Обработчик] Отправка ответа в Kafka...")
    send_message_to_kafka(
        topic="auth.balance.reserve.response.shop",
        payload={
            "transaction_id": transaction_id,
            "user_id": user_id,
            "success": transaction.status == TransactionStatus.RESERVED,
            "error_message": error_message
        },
        target_service="shop"
    )
