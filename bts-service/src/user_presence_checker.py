import time
import logging
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserPresenceChecker:
    """
    Periodically checks user presence (TTL-backed keys) and reconciles the owner-scoped
    connected-user SET. Then recomputes current load and stores BTS status in Redis.

    Requirements:
      - user_cache is an owner-specific UserRedisCache with:
          - redis_client
          - _users_set_key (e.g. "bts:{owner}:users")
          - _user_key_prefix (e.g. "bts:{owner}:user:")
          - get_connected_imeis()
      - bts_status_cache is a BtsStatusRedisCache with set_status(...)
    """

    def __init__(
        self,
        *,
        user_cache,
        bts_status_cache,
        owner_bts_id: str,
        capacity: int,
        overload_threshold: float = 0.8,
        check_interval: int = 3,
    ):
        self.user_cache = user_cache
        self.bts_status_cache = bts_status_cache
        self.owner_bts_id = str(owner_bts_id)
        self.capacity = int(capacity)
        self.overload_threshold = float(overload_threshold)
        self.check_interval = int(check_interval)
        self._running = False

    def start_checking(self):
        """Start presence checking in a background thread."""
        self._running = True
        thread = Thread(target=self._check_loop, daemon=True)
        thread.start()
        logger.info("UserPresenceChecker started")

    def stop_checking(self):
        """Stop presence checking."""
        self._running = False

    def _compute_status(self, load: int) -> str:
        if self.capacity <= 0:
            return "unknown"
        if (load / self.capacity) >= self.overload_threshold:
            return "overloaded"
        return "active"

    def _remove_stale_users_from_set(self, imeis: list[str]) -> int:
        """
        For each IMEI in the owner SET, check if its presence key exists.
        Remove those without presence key from the owner SET.

        Returns:
            number of removed IMEIs
        """
        if not imeis:
            return 0

        # Pipeline EXISTS checks
        pipe = self.user_cache.redis_client.pipeline(transaction=False)
        for imei in imeis:
            pipe.exists(f"{self.user_cache._user_key_prefix}{imei}")
        exists_results = pipe.execute()

        stale_imeis = [imei for imei, exists in zip(imeis, exists_results) if not exists]
        if not stale_imeis:
            return 0

        # Pipeline removals
        pipe = self.user_cache.redis_client.pipeline(transaction=False)
        for imei in stale_imeis:
            pipe.srem(self.user_cache._users_set_key, imei)
        pipe.execute()

        return len(stale_imeis)

    def _recalculate_load(self) -> int:
        """Recompute current load from the owner-scoped connected-user SET size."""
        return int(self.user_cache.redis_client.scard(self.user_cache._users_set_key))

    def _store_bts_status(self, load: int) -> None:
        """Compute and store BTS status for this owner BTS in Redis."""
        status = self._compute_status(load)
        self.bts_status_cache.set_status(
            bts_id=self.owner_bts_id,
            status=status,
            capacity=self.capacity,
            load=load,
        )

    def _check_loop(self):
        """Continuously run presence checks and update BTS status."""
        while self._running:
            try:
                imeis = list(self.user_cache.get_connected_imeis())

                removed = self._remove_stale_users_from_set(imeis)
                load = self._recalculate_load()
                self._store_bts_status(load)

                if removed:
                    logger.info(
                        f"UserPresenceChecker: removed={removed} stale users, load={load}"
                    )
                else:
                    logger.info(f"UserPresenceChecker: load={load}")

            except Exception as e:
                logger.error(f"UserPresenceChecker failed: {e}")

            time.sleep(self.check_interval)
