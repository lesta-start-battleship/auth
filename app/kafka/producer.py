import json

from confluent_kafka import Producer
from config import logger, KAFKA_ADDRESS

producer = Producer({'bootstrap.servers': KAFKA_ADDRESS})


def send_message_to_kafka(
    topic: str, payload: dict, target_service: str = "?"
) -> None:
    log_prefix = f"AUTH -> Kafka -> {target_service.upper()}"
    logger.info(
        f"[Kafka Продюсер: {log_prefix}] Отправка сообщения в топик '{topic}': {payload}"
    )
    try:
        producer.produce(topic, json.dumps(payload).encode("utf-8"))
        producer.flush()
        logger.info(
            f"[Kafka Продюсер: {log_prefix}] Сообщение успешно отправлено в '{topic}'"
        )
    except Exception as e:
        logger.error(f"[Kafka Продюсер]: {log_prefix} Ошибка при отправке в '{topic}': {e}")
