import socket
import json
import time
import os
import logging
from threading import Thread
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Broadcaster:
    def __init__(self):
        self.broadcast_address = '255.255.255.255'
        self.broadcast_port = 5000
        self.bts_id = os.getenv('BTS_ID', 'BTS001')
        self.lac = os.getenv('BTS_LAC', '1001')
        self.location_x = float(os.getenv('BTS_LOCATION_X', 100))
        self.location_y = float(os.getenv('BTS_LOCATION_Y', 100))
        self.port = int(os.getenv('BTS_PORT', 8080))
        self.broadcast_interval = 3

        interfaces = socket.getaddrinfo(
            host=socket.gethostname(), port=None, family=socket.AF_INET)
        self.host = interfaces[0][-1][0]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.running = False

    def start(self):
        """Start beacon broadcasting in a background thread."""
        self.running = True
        thread = Thread(target=self._broadcast_loop, daemon=True)
        thread.start()
        logger.info(f"Broadcaster started for {self.bts_id}")

    def stop(self):
        """Stop broadcasting."""
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def _broadcast_loop(self):
        """Continuously send beacon messages."""
        while self.running:
            try:
                x, y = self.location_x, self.location_y
                beacon = {
                    'time': datetime.now().isoformat(),
                    'bts_id': self.bts_id,
                    'lac': self.lac,
                    'bts_location': {
                        'x': x,
                        'y': y
                    },
                    'connect': {
                        'ip': self.host,
                        'port': self.port
                    }
                }

                message = json.dumps(beacon).encode('utf-8')
                self.sock.sendto(
                    message, (self.broadcast_address, self.broadcast_port))
                logger.info(f"Beacon sent: {self.bts_id} @ ({x}, {y})")

            except Exception as e:
                logger.error(f"Failed to send beacon: {e}")

            time.sleep(self.broadcast_interval)
