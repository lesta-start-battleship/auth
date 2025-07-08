import json
from datetime import datetime
from database.models import DeviceLogin
from config import logger

from database.models import OAuthProvider


class DeviceLoginCache:
    def __init__(self, redis_instance) -> None:
        self.redis = redis_instance

    def set(
        self,
        device_code: str,
        provider: OAuthProvider | str,
        expires_at: datetime,
        is_verified: bool = False,
        user_id: int | None = None,
        min_ttl: int = 10
    ) -> None:
        ttl = int((expires_at - datetime.utcnow()).total_seconds())

        if ttl <= 0:
            ttl = min_ttl
            logger.warning(
                f"TTL для device_code={device_code} был < 0, используется fallback TTL={min_ttl} секунд"
            )

        self.redis.setex(
            device_code,
            ttl,
            json.dumps({
                "provider": provider.value if isinstance(provider, OAuthProvider) else provider,
                "expires_at": expires_at.timestamp(),
                "is_verified": is_verified,
                "user_id": user_id,
            })
        )
        logger.info(
            f"Запись с device_code={device_code} успешно сохранена в кэш Redis на {ttl} секунд"
        )

    def get(self, device_code: str) -> DeviceLogin | None:
        raw = self.redis.get(device_code)

        if not raw:
            logger.info(f"Кэш для device_code={device_code} не найден")
            return None
        try:
            data = json.loads(raw)
            login_record = DeviceLogin(
                device_code=device_code,
                provider=OAuthProvider(data["provider"]),
                expires_at=datetime.fromtimestamp(data["expires_at"]),
                is_verified=data["is_verified"],
                user_id=data["user_id"]
            )
            logger.info(f"Кэш для device_code={device_code} успешно получен")

            return login_record
        except Exception as e:
            logger.error(f"Не удалось десериализовать запись в кэше: {str(e)}")
            return None

    def update(
        self,
        device_code: str,
        provider: OAuthProvider | str,
        expires_at: datetime,
        user_id: int
    ) -> None:
        ttl = int((expires_at - datetime.utcnow()).total_seconds())

        if ttl > 0:
            logger.info(f"Обновление кэша для device_code={device_code}")
            self.set(
                device_code, provider, expires_at,
                is_verified=True, user_id=user_id
            )
        else:
            logger.warning(
                f"Попытка обновить кэш с истёкшим TTL для device_code={device_code} пропущена"
            )

    def delete(self, device_code):
        self.redis.delete(device_code)
        logger.info(f"Кэш для device_code={device_code} успешно удалён")
