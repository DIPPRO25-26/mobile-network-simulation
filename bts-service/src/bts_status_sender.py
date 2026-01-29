import time
import logging
import asyncio
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BtsStatusSender:
    def __init__(self, send_bts_status_to_central_backend_async, cache, owner_bts_id: str, send_interval=3):
        """
        Sends ONLY this BTS owner's status to Central Backend.

        :param send_bts_status_to_central_backend_async: async fn(data: dict) -> dict
        :param cache: owner-namespaced status cache (e.g., BtsStatusRedisCache) with get_status(bts_id) -> dict|None
        :param owner_bts_id: this BTS's id (the only status we send)
        :param send_interval: seconds between send cycles
        """
        self.send_bts_status_to_central_backend_async = send_bts_status_to_central_backend_async
        self.cache = cache
        self.owner_bts_id = str(owner_bts_id)
        self.send_interval = send_interval
        self.running = False

    def start(self):
        """Start sending in a background thread."""
        self.running = True
        thread = Thread(target=self._send_loop, daemon=True)
        thread.start()
        logger.info("BtsStatusSender started")

    def stop(self):
        """Stop sending."""
        self.running = False

    def _send_loop(self):
        """Continuously send ONLY owner BTS status to Central Backend."""
        while self.running:
            try:
                status = self.cache.get_status(self.owner_bts_id)

                if not status:
                    logger.debug(f"BtsStatusSender: no cached status for owner {self.owner_bts_id}")
                else:
                    # Central backend expects btsId (camelCase), so map if needed
                    payload = dict(status)
                    if "btsId" not in payload and "bts_id" in payload:
                        payload["btsId"] = payload.pop("bts_id")

                    asyncio.run(self.send_bts_status_to_central_backend_async(self.owner_bts_id, payload))
                    logger.debug(f"BtsStatusSender sent owner status for {self.owner_bts_id}")

            except Exception as e:
                logger.error(f"BtsStatusSender failed to send owner BTS status: {e}")

            time.sleep(self.send_interval)