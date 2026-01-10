import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)


class UserRedisCache:
    """
    Observer that persists user metadata to Redis when connection or keepalive events occur.
    Owner-specific: keys are namespaced by owner_bts_id.
    """

    def __init__(self, redis_client, ttl: int, owner_bts_id: str):
        self.redis_client = redis_client
        self.ttl = ttl
        self.owner_bts_id = owner_bts_id

        # Owner-scoped keys
        self._users_set_key = f"bts:{self.owner_bts_id}:users"
        self._user_key_prefix = f"bts:{self.owner_bts_id}:user:"

    def update(self, event: str, data: dict):
        if event in ("user_connected", "user_keepalive"):
            self._store_metadata(
                imei=data["imei"],
                location=data["location"],
                bts_id=data["bts_id"],
                timestamp=data["timestamp"]
            )

    def _store_metadata(self, imei: str, location: dict, bts_id: str, timestamp: str):
        user_key = f"{self._user_key_prefix}{imei}"

        try:
            pipe = self.redis_client.pipeline(transaction=False)

            # Track membership in this BTS' connected users set (idempotent)
            pipe.sadd(self._users_set_key, imei)

            # Store metadata under owner namespace
            pipe.hset(user_key, mapping={
                "last_seen": timestamp,
                "bts_id": bts_id,
                "location_x": str(location["x"]),
                "location_y": str(location["y"]),
            })
            pipe.expire(user_key, self.ttl)

            pipe.execute()
            logger.debug(
                f"Redis: Cached metadata for {imei} under {self.owner_bts_id} (TTL {self.ttl}s)"
            )
        except Exception as e:
            logger.error(f"Redis: Failed to cache metadata for {imei}: {e}")

    def get_metadata(self, imei: str) -> Optional[dict]:
        user_key = f"{self._user_key_prefix}{imei}"
        try:
            data = self.redis_client.hgetall(user_key)
            if not data:
                return None
            return {
                "last_seen": data.get("last_seen"),
                "bts_id": data.get("bts_id"),
                "location": {
                    "x": float(data.get("location_x", "0")),
                    "y": float(data.get("location_y", "0")),
                },
            }
        except Exception as e:
            logger.error(f"Redis: Failed to get metadata for {imei}: {e}")
            return None

    def get_ttl(self, imei: str) -> int:
        user_key = f"{self._user_key_prefix}{imei}"
        return self.redis_client.ttl(user_key)

    def get_connected_imeis(self) -> set[str]:
        return set(self.redis_client.smembers(self._users_set_key))

    def remove_connected_imei(self, imei: str) -> None:
        self.redis_client.srem(self._users_set_key, imei)

    def connected_count(self) -> int:
        return int(self.redis_client.scard(self._users_set_key))

class BtsInformationRedisCache:
    """
    Caches neighbour BTS information into Redis, namespaced per *owner* BTS.

    Stores (per owner BTS):
        hash key:  bts_id:{owner_bts_id}:bts_neighbours:{neighbour_bts_id}:information
        index set: bts_id:{owner_bts_id}:bts_neighbours:index
    """

    def __init__(self, redis_client, ttl: int, owner_bts_id: str):
        self.redis_client = redis_client
        self.ttl = ttl
        self.owner_bts_id = str(owner_bts_id)
        self._index_key = f"bts_id:{self.owner_bts_id}:bts_neighbours:index"

    def _information_key(self, neighbour_bts_id: str) -> str:
        return f"bts_id:{self.owner_bts_id}:bts_neighbours:{neighbour_bts_id}:information"

    def update(self, event: str, data: dict) -> None:
        if event != "bts_info_updated":
            return

        neighbour_id = str(data.get("btsId", "")).strip()
        if not neighbour_id:
            return

        key = self._information_key(neighbour_id)
        try:
            self.redis_client.hset(
                key,
                mapping={
                    "btsId": str(data.get("btsId", "")),
                    "mcc": str(data.get("mcc", "")),
                    "mnc": str(data.get("mnc", "")),
                    "lac": str(data.get("lac", "")),
                    "locationX": str(data.get("locationX", "")),
                    "locationY": str(data.get("locationY", "")),
                    "status": str(data.get("status", "")),
                    "maxCapacity": str(data.get("maxCapacity", "")),
                    "currentLoad": str(data.get("currentLoad", "")),
                    "updatedAt": str(data.get("updatedAt", "")),
                    "createdAt": str(data.get("createdAt", "")),
                },
            )
            self.redis_client.expire(key, self.ttl)

            # track neighbour ids for *this* owner BTS only
            self.redis_client.sadd(self._index_key, neighbour_id)

        except Exception as e:
            logger.error(f"Redis: Failed to cache neighbour {neighbour_id} for {self.owner_bts_id}: {e}")


    def get(self, neighbour_bts_id: str):
        key = self._information_key(str(neighbour_bts_id))
        try:
            data = self.redis_client.hgetall(key)
            return data or None
        except Exception as e:
            logger.error(f"Redis: Failed to get neighbour {neighbour_bts_id} for {self.owner_bts_id}: {e}")
            return None
        
    def get_all(self):
        try:
            ids = self.redis_client.smembers(self._index_key)
            if not ids:
                return []

            results = []
            stale = []

            for neighbour_id in ids:
                if isinstance(neighbour_id, bytes):
                    neighbour_id = neighbour_id.decode("utf-8")

                data = self.get(neighbour_id)
                if data:
                    results.append(data)
                else:
                    stale.append(neighbour_id)

            if stale:
                self.redis_client.srem(self._index_key, *stale)

            return results

        except Exception as e:
            logger.error(f"Redis: Failed to get all neighbours for {self.owner_bts_id}: {e}")
            return []
        
class BtsStatusRedisCache:
    """
    Stores BTS status records in Redis, namespaced by an owner (e.g. "this BTS").

    Key pattern:
        bts_id:{owner_bts_id}:bts_status:{bts_id}

    Fields stored (only):
        bts_id, status, capacity, load
    """

    def __init__(self, redis_client, ttl: int, owner_bts_id: str):
        self.redis_client = redis_client
        self.ttl = ttl
        self.owner_bts_id = str(owner_bts_id)

    def _status_key(self, bts_id: str) -> str:
        return f"bts_id:{self.owner_bts_id}:bts_status:{str(bts_id)}"

    def set_status(self, bts_id: str, status: str, capacity: int, load: int) -> None:
        """
        Store ONLY BTS status fields for a given bts_id (under this owner's namespace).
        Fields: bts_id, status, capacity, load
        """
        if not bts_id:
            return

        key = self._status_key(bts_id)
        try:
            self.redis_client.hset(
                key,
                mapping={
                    "bts_id": str(bts_id),
                    "status": str(status),
                    "capacity": str(int(capacity)),
                    "load": str(int(load)),
                },
            )
            self.redis_client.expire(key, self.ttl)
        except Exception as e:
            logger.error(f"Redis: Failed to set status for {bts_id} (owner {self.owner_bts_id}): {e}")

    def get_status(self, bts_id: str) -> Optional[dict[str, str]]:
        """Return status dict for bts_id (under this owner's namespace) or None."""
        if not bts_id:
            return None

        key = self._status_key(bts_id)
        try:
            data = self.redis_client.hgetall(key)
            return data or None
        except Exception as e:
            logger.error(f"Redis: Failed to get status for {bts_id} (owner {self.owner_bts_id}): {e}")
            return None
        