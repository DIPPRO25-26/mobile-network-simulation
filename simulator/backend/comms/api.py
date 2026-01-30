from threading import Thread
import random
import sys
from hashlib import sha256
import httpx
from comms.bts_discovery import scan_bts, closest_bts
import traceback


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

def get_bts_map():
    return bts_map

last_bts = dict()

# switched to go-inspired errors
# not a fan, but exception handling isnt the best with async generators
async def connect(timestamp, imei, x, y):
    if len(bts_map) == 0:
        return {"error": "No BTS found", "detail": "No BTS found (at all)"}
    last = last_bts.get(imei)

    if last is None or last not in bts_map:
        last = closest_bts(x, y, bts_map)
        last_bts[imei] = last
        if last is None:
            return {"error": "No BTS found", "detail": "No BTS found (in signal range)"}
    print(f"Connecting to BTS: {last}", file=sys.stderr)

    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    req_json = {"imei": imei, "timestamp": timestamp,
            "user_location": {"x": x, "y": y}}

    conn = bts_map[last]["connect"]

    url = f"http://{conn['ip']}:{conn['port']}/api/v1/connect"
    try:
        async with httpx.AsyncClient() as client:
            d = await client.post(url, json=req_json, timeout=3.0)
            print("LOGLOGLOG", d.status_code, d.text)
            d = d.json()
    except httpx.TimeoutException, Exception:
        traceback.print_exc()
        old = last
        last_bts[imei] = None
        print(f"Connection to BTS ({last}) failed. Removing from bts_map", file=sys.stderr)
        return {"error": "Connect timeout", "detail": f"Connecting to {last} failed"}
    print(d, file=sys.stderr)
    if d.get('status') != "success":
        print(f"Error response from bts: {d}", file=sys.stderr)
        last_bts[imei] = None
        return {"error": "Non-success status from bts", 
                "detail": f"{last} returned non-success status: {d.get('status')}", 
                "response": d}
    # if d["data"]["action"] == "handover":
    #     # use target bts if provided, or closest bts that isnt current.
    #     # this creates a loop if both closest bts-es want us to handover,
    #     # but dont provide targets
    #     target = d["data"]["target_bts_id"] or \
    #                closest_bts(x, y, {k:v for k,v in bts_map.items() if k != last})
    #     print(f"handover requested from bts, next request will be towards {target}", file=sys.stderr)
    #     last_bts[imei] = target
    return {"error": None, "detail": f"Connected successfully to {last}", "response": d}
    

async def send_keep_alive(x, y, imei, timestamp):
    if len(bts_map) == 0:
        return {"error": "No BTS found", "detail": "No BTS found (at all)"}
    last = last_bts.get(imei)

    if last is None or last not in bts_map:
        last = closest_bts(x, y, bts_map)
        last_bts[imei] = last
    print(f"Sending keep alive to BTS: {last}", file=sys.stderr)

    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    json = {"imei": imei, "timestamp": timestamp,
            "user_location": {"x": x, "y": y}}
    
    conn = bts_map[last]["connect"]

    url = f"http://{conn['ip']}:{conn['port']}/api/v1/keepalive"
    try:
        async with httpx.AsyncClient() as client:
            d = await client.post(url, json=json, timeout=3.0)
            d = d.json()
    except httpx.TimeoutException:
        last_bts[imei] = None
        print(f"Sending keep alive to BTS ({last}) failed. Removing from bts_map", file=sys.stderr)
        return {"error": "Connect timeout", "detail": f"Sending keep alive to {last} failed"}
    print(d, file=sys.stderr)
    if d.get('status') != "success":
        print(f"Error response from bts: {d}", file=sys.stderr)
        return {"error": "Non-success status from bts", 
                "detail": f"{last} returned non-success status: {d.get('status')}", 
                "response": d}
    if d["data"]["action"] == "handover":
        # use target bts if provided, or closest bts that isnt current.
        # this creates a loop if both closest bts-es want us to handover,
        # but dont provide targets
        target = d["data"]["target_bts_id"] or \
                   closest_bts(x, y, {k:v for k,v in bts_map.items() if k != last})
        print(f"handover requested from bts, next request will be towards {target}", file=sys.stderr)
        last_bts[imei] = target
        return {"error": None, 
                "detail": f"Sent keep alive successfully to {last}, asked to handover",
                "action": "handover",
                "response": d}
    
    return {"error": None, "detail": f"Sent keep alive successfully to {last}", "response": d}
