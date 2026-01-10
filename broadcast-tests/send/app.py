import socket
import sys
import os
import json
from time import sleep
from datetime import datetime
import random

bts_id = os.environ["BTS_ID"]
pos_x, pos_y = os.environ["BTS_LOC_X"], os.environ["BTS_LOC_Y"]


def main():
    r = random.random()*3
    print(f"sleeping {r}", file=sys.stderr)
    sleep(r)

    interfaces = socket.getaddrinfo(
        host=socket.gethostname(), port=None, family=socket.AF_INET)
    ip = interfaces[0][-1][0]
    print(f"Sending on ip {ip}", file=sys.stderr)

    while True:
        msg = json.dumps({"time": datetime.now().isoformat(),
                          "bts_id": bts_id,
                          "bts_location": {"x": pos_x, "y": pos_y},
                          "ip": ip})
        print(f'sending {msg}', file=sys.stderr)
        msg = msg.encode()
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((ip, 0))
        sock.sendto(msg, ("255.255.255.255", 5000))
        sock.close()

        sleep(2)


main()
