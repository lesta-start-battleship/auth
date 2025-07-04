import json

from confluent_kafka import Consumer, Producer
from sqlalchemy.orm import Session

from database.models import (
    UserCurrency, UserTransaction, CurrencyType, TransactionStatus
)

producer = Producer({'bootstrap.servers': 'kafka:9092'})


def send_kafka(topic: str, payload: dict):
    producer.produce(topic, json.dumps(payload).encode("utf-8"))
    producer.flush()


def handle_balance_reserve(db: Session, msg: dict):
    transaction_id = msg['transaction_id']
    user_id = msg['user_id']
    amount = msg['amount']
    currency = CurrencyType(msg['currency_type'])

    user_currency = db.query(UserCurrency).filter_by(user_id=user_id).first()
    transaction = UserTransaction(
        transaction_id=transaction_id,
        user_id=user_id,
        currency_type=currency,
        amount=amount,
        status=TransactionStatus.PENDING
    )

    if not user_currency:
        transaction.status = TransactionStatus.DECLINED
    else:
        available = getattr(user_currency, currency.value)
        if available >= amount:
            setattr(user_currency, currency.value, available - amount)
            transaction.status = TransactionStatus.RESERVED
        else:
            transaction.status = TransactionStatus.DECLINED

    db.add(transaction)
    db.commit()

    send_kafka("balance-responses", {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "success": transaction.status == TransactionStatus.RESERVED
    })


def handle_balance_compensate(db: Session, msg: dict):
    transaction_id = msg['transaction_id']
    user_id = msg['user_id']
    amount = msg['amount']
    currency = CurrencyType(msg['currency_type'])

    transaction = db.query(UserTransaction).filter_by(
        transaction_id=transaction_id, user_id=user_id
    ).first()
    user_currency = db.query(UserCurrency).filter_by(user_id=user_id).first()

    success = False
    if transaction and user_currency:
        setattr(
            user_currency,
            currency.value,
            getattr(user_currency, currency.value) + amount
        )
        transaction.status = TransactionStatus.FAILED
        db.commit()
        success = True

    send_kafka("compensation-responses", {
        "transaction_id": transaction_id,
        "user_id": user_id,
        "success": success
    })


def handle_balance_complete(db: Session, msg: dict):
    transaction_id = msg['transaction_id']

    transaction = db.query(UserTransaction).filter_by(
        transaction_id=transaction_id).first()
    success = False

    if transaction and transaction.status == TransactionStatus.RESERVED:
        transaction.status = TransactionStatus.COMPLETED
        db.commit()
        success = True

    send_kafka("balance-complete-responses", {"success": success})


def start_consumer_loop(db: Session):
    consumer = Consumer({
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'auth-service-group',
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([
        'balance-reserve-commands',
        'balance-compensate-commands',
        'balance-complete-commands'
    ])

    print("Balance transaction consumer is running...")

    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue

        value = msg.value()

        if not value:
            continue

        try:
            data = json.loads(value.decode("utf-8"))
            topic = msg.topic()

            if topic == "balance-reserve-commands":
                handle_balance_reserve(db, data)
            elif topic == "balance-compensate-commands":
                handle_balance_compensate(db, data)
            elif topic == "balance-complete-commands":
                handle_balance_complete(db, data)

        except Exception as e:
            print(f"Error handling Kafka message: {e}")
