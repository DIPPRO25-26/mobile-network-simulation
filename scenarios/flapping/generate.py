import sys, os
sys.path.insert(0, os.path.abspath('..'))

from utils import gen_imei
from datetime import datetime, timedelta, UTC

positions_x = [185, 205, 215, 195]

imei = gen_imei()

cur_time = datetime.now(UTC)

log = []
filename = "flapping.csv"
delta = timedelta(seconds=1)
with open(filename, 'w') as f:
    f.write("timestamp,imei,x,y\n")
    y = 40
    for _ in range(4):
        for x in positions_x:
            y += 3
            f.write(f"{cur_time.isoformat()},{imei},{x},{y}\n")
            cur_time += delta
print(f"written to {filename}")



