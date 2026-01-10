import time
import logging
import asyncio
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BtsStatusPoller:
    def __init__(self, fetch_all_bts_info_async, observer, owner_bts_id, poll_interval=3):
        self.fetch_all_bts_info_async = fetch_all_bts_info_async
        self.observer = observer
        self.owner_bts_id = str(owner_bts_id)
        self.poll_interval = poll_interval
        self.running = False

    def start(self):
        """Start polling in a background thread."""
        self.running = True
        thread = Thread(target=self._poll_loop, daemon=True)
        thread.start()
        logger.info("BtsStatusPoller started")

    def stop(self):
        """Stop polling."""
        self.running = False

    def _poll_loop(self):
        """Continuously poll Central Backend and cache neighbour BTS information."""
        while self.running:
            try:
                result = asyncio.run(self.fetch_all_bts_info_async())

                # Accept either list[dict] or {"data": list[dict]}
                if isinstance(result, dict):
                    bts_list = result.get("data", [])
                else:
                    bts_list = result or []

                for bts in bts_list:
                    if not isinstance(bts, dict):
                        continue
                    if "btsId" not in bts:
                        continue
                    if str(bts.get("btsId")) == self.owner_bts_id:
                        continue

                    self.observer.update(event="bts_info_updated", data=bts)

                logger.debug(f"BtsStatusPoller refreshed {len(bts_list)} BTS entries")

            except Exception as e:
                logger.error(f"BtsStatusPoller failed to refresh BTS status: {e}")

            time.sleep(self.poll_interval)
