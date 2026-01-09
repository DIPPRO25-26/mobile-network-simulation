import random

def gen_imei():
    return random.randint(10**14, 10**15 - 1)


def connect(X, Y, imei, timestamp):
    return {
        "imei": imei,
        "timestamp": timestamp,
        "location": (X, Y),
        "event": "connect"
    }