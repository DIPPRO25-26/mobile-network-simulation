import math
import socket
import sys
import json
from datetime import datetime, timedelta

UDP_PORT = 5000


def scan_bts(bts_map):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", UDP_PORT))

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            data = json.loads(data.decode("utf-8"))
            bts_id = data["bts_id"]
            data["last_ping"] = datetime.fromisoformat(data["time"])
            del data["time"]
            bts_map[bts_id] = data
            now = datetime.now()
            for k in bts_map.keys():
                if bts_map[k]["last_ping"] - now > timedelta(seconds=30):
                    del bts_map[k]
        except Exception as e:
            print(f"Error in bts listener: {e}", file=sys.stderr)


def dist(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.hypot(x2-x1, y2-y1)


def closest_bts(x, y, bts_map):
    min_d = 1e10
    min_bts_id = None
    for k, v in bts_map.items():
        p1 = (x, y)
        p2 = (v["bts_location"]["x"], v["bts_location"]["y"])
        d = dist(p1, p2)
        if d < min_d:
            min_d = d
            min_bts_id = k
    return min_bts_id
