from threading import Thread
import random
import sys
import time
from hashlib import sha256
import requests as r
from comms.bts_discovery import scan_bts, closest_bts
from comms.hmac import create_hmac_headers

def calc_luhn(i):
    s = [*map(int, i)]
    total = 0
    for i, x in enumerate(s):
        if i % 2:
            # zbroj znamenki (dvoznamenkastog broja)
            total += (x*2) // 10 + (x*2) % 10
        else:
            total += x
    return (10 - total) % 10


# http://tacdb.osmocom.org/
with open("tacdb.csv", "r") as f:
    data = f.readlines()
    taclist = [x.split(',')[0] for x in data]


def gen_imei():
    tac = random.choice(taclist)
    serial = random.randint(10**5, 10**6-1)
    x = f"{tac}{serial}"
    check_digit = calc_luhn(x)
    return f"{x}{check_digit}"


def sign(*args):
    return sha256(",".join(map(str, args)).encode()).hexdigest()


bts_map = dict()
bts_thread = Thread(target=scan_bts, args=(bts_map,), daemon=True)
bts_thread.start()

last_bts = dict()


class NoBTSAvailable(Exception):
    pass


class ConnectError(Exception):
    pass


def connect(x, y, imei, timestamp):
    if len(bts_map) == 0:
        raise NoBTSAvailable("No BTS found")
    last = last_bts.get(imei)

    if last is None or last not in bts_map:
        last = closest_bts(x, y, bts_map)
        last_bts[imei] = last
    print(f"Connecting to BTS: {last}", file=sys.stderr)

    json = {"imei": imei, "timestamp": timestamp,
            "user_location": {"x": x, "y": y}}
    headers = create_hmac_headers(json)
    conn = bts_map[last]["connect"]
    url = f"http://{conn['ip']}:{conn['port']}/api/v1/connect"
    d = r.post(url, json=json, headers=headers)
    d = d.json()
    print(d, file=sys.stderr)
    if d.get('status') != "success":
        print("Error response from bts")
        return
    if d["data"]["action"] == "handover":
        # use target bts if provided, or closest bts that isnt current.
        # this creates a loop if both closest bts-es want us to handover,
        # but dont provide targets
        target = d["data"]["target_bts_id"] or \
                   closest_bts(x, y, {k:v for k,v in bts_map.items() if k != last})
        print(f"handover requested from bts, next request will be towards {target}", file=sys.stderr)
        last_bts[imei] = target



if __name__ == "__main__":
    for _ in range(10):
        x = gen_imei()
        print(x)
        connect(x, random.randint(1, 3), random.randint(1000, 4000))
