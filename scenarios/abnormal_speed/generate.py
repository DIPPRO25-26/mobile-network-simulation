import sys, os
sys.path.insert(0, os.path.abspath('..'))

from utils import gen_imei
from datetime import datetime, timedelta, UTC

positions = [(20, 20), (180, 180)]

imei = gen_imei()

cur_time = datetime.now(UTC)

log = []
filename = "abnormal_speed.csv"
delta = timedelta(seconds=1)
with open(filename, 'w') as f:
    f.write("timestamp,imei,x,y\n")
    for _ in range(4):
        for x,y in positions:
            f.write(f"{cur_time.isoformat()},{imei},{x},{y}\n")
            cur_time += delta
print(f"written to {filename}")



