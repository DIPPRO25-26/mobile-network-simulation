import sys, os
sys.path.insert(0, os.path.abspath('..'))

from utils import gen_imei
from datetime import datetime, timedelta, UTC
import random

cur_time = datetime.now(UTC)

filename = "overload.csv"
delta = timedelta(seconds=0.2)
with open(filename, 'w') as f:
    f.write("timestamp,imei,x,y\n")
    for _ in range(150):
        imei = gen_imei()
        x, y = random.randint(20, 180), random.randint(20, 180)
        f.write(f"{cur_time.isoformat()},{imei},{x},{y}\n")
        cur_time += delta
print(f"written to {filename}")



