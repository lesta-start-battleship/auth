import json

from confluent_kafka import Consumer
from database.database import session
from config import logger, KAFKA_ADDRESS
from kafka.handlers.balance_reserve import handle_balance_reserve
from kafka.handlers.balance_compensate import handle_balance_compensate


def start_consumer_loop() -> None:
    consumer = Consumer({
        "bootstrap.servers": KAFKA_ADDRESS,
        "group.id": "auth-service-group",
        "auto.offset.reset": "earliest"
    })
    consumer.subscribe([
        "shop.balance.reserve.request.auth",
        "shop.balance.compensate.request.auth"
    ])

    logger.info("[Kafka Консьюмер] Запущен обработчик транзакций...")
    while True:
        try:
            msg = consumer.poll(1.0)
        except Exception as e:
            logger.error(f"[Kafka Консьюмер] Ошибка при получении сообщения: {e}")
            continue

        if msg is None:
            continue

        value = msg.value()
        if not value:
            logger.warning(
                f"[Kafka Консьюмер] Пустое сообщение на топике '{msg.value()}', пропуск"
            )
            continue

        decoded = value.decode("utf-8")
        if decoded.startswith("Subscribed topic not available"):
            logger.error(f"[Kafka Консьюмер] Ошибка брокера: {decoded}")
            continue

        logger.info(
            f"[Kafka Консьюмер] Получено сообщение на топике '{msg.topic()}': {decoded}"
        )
        try:
            data = json.loads(decoded)
        except json.JSONDecodeError as e:
            logger.error(
                f"[Kafka Консьюмер] Ошибка парсинга JSON: {e}: {decoded}")
            continue

        try:
            topic = msg.topic()
            db = session()

            if topic == "shop.balance.reserve.request.auth":
                logger.info(
                    "[Kafka Консьюмер] Обработка запроса на резервирование баланса от shop"
                )
                handle_balance_reserve(db, data)
            elif topic == "shop.balance.compensate.request.auth":
                logger.info(
                    "[Kafka Консьюмер] Обработка запроса на компенсацию баланса от shop"
                )
                handle_balance_compensate(db, data)
            else:
                logger.warning(f"[Kafka Консьюмер] Неизвестный топик: {topic}")
        except Exception as e:
            logger.error(f"[Kafka Консьюмер] Ошибка при обработке сообщения: {e}")
