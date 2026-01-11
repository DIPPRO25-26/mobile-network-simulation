import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Observer that persists user metadata to Redis when connection events occur.
    """

    def __init__(self, redis_client, ttl: int):
        self.redis_client = redis_client
        self.ttl = ttl

    def update(self, event: str, data: dict):
        """React to user connection event by storing in Redis"""
        if event == "user_connected":
            self._store_metadata(
                imei=data["imei"],
                location=data["location"],
                bts_id=data["bts_id"],
                timestamp=data["timestamp"]
            )

    def _store_metadata(self, imei: str, location: dict, bts_id: str, timestamp: str):
        """Store user metadata in Redis"""
        key = f"imei:{imei}"

        try:
            self.redis_client.hset(key, mapping={
                "last_seen": timestamp,
                "bts_id": bts_id,
                "location_x": str(location["x"]),
                "location_y": str(location["y"])
            })
            self.redis_client.expire(key, self.ttl)
            logger.debug(f"Redis: Cached metadata for {imei} (TTL {self.ttl}s)")
        except Exception as e:
            logger.error(f"Redis: Failed to cache metadata for {imei}: {e}")

    def get_metadata(self, imei: str) -> Optional[dict]:
        """Query Redis for user metadata"""
        key = f"imei:{imei}"
        try:
            data = self.redis_client.hgetall(key)
            if not data:
                return None
            return {
                "last_seen": data.get("last_seen"),
                "bts_id": data.get("bts_id"),
                "location": {
                    "x": float(data.get("location_x", "0")),
                    "y": float(data.get("location_y", "0"))
                }
            }
        except Exception as e:
            logger.error(f"Redis: Failed to get metadata for {imei}: {e}")
            return None

    def get_ttl(self, imei: str) -> int:
        """Get remaining TTL"""
        key = f"imei:{imei}"
        return self.redis_client.ttl(key)
