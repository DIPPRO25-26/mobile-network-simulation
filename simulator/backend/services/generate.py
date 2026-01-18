from datetime import datetime
from comms.api import gen_imei, connect
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import X_MAX, X_MIN, Y_MAX, Y_MIN
import random
import time
import asyncio
import math
from aiostream import stream


async def simulate_actions(imei, num_actions):
    x = float(random.randint(X_MIN, X_MAX))
    y = float(random.randint(Y_MIN, Y_MAX))
    
    base_speed = random.uniform(5.0, 30.0)

    for _ in range(num_actions):
        if random.random() < 0.15:
            pass
        else:
            while True:
                angle = random.uniform(0, 2 * math.pi)
                step_size = base_speed * random.uniform(0.75, 1.25)

                new_x = x + step_size * math.cos(angle)
                new_y = y + step_size * math.sin(angle)

                if X_MIN <= new_x <= X_MAX and Y_MIN <= new_y <= Y_MAX:
                    x = new_x
                    y = new_y
                    break

        timestamp = datetime.now()
        
        final_x, final_y = int(x), int(y)

        response = await connect(timestamp, imei, final_x, final_y)
        yield {
            "timestamp": timestamp, "imei": imei, 
            "x": final_x, "y": final_y, 
            "response": response
        }
        await asyncio.sleep(random.random() * 2)


async def generate(num_users, num_actions):
    imeis = [gen_imei() for _ in range(num_users)]
    tasks = [simulate_actions(imei, num_actions) for imei in imeis]
    
    combined = stream.merge(*tasks)
    async with combined.stream() as streamer:
        async for item in streamer:
            yield item
