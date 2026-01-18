from datetime import datetime
from comms.api import gen_imei, connect
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import X_MAX, X_MIN, Y_MAX, Y_MIN
import random
import time
import asyncio
from aiostream import stream


async def simulate_actions(imei, num_actions):
    x = random.randint(X_MIN, X_MAX)
    y = random.randint(Y_MIN, Y_MAX)

    for _ in range(num_actions):
        if random.random() < 0.3:  # chance to stay at same location
            pass
        else:
            direction = random.choice(['up', 'down', 'left', 'right',
                                       'diagonal_up_right', 'diagonal_up_left',
                                       'diagonal_down_right', 'diagonal_down_left'])
            if direction == 'up':
                y += 1
            elif direction == 'down':
                y -= 1
            elif direction == 'left':
                x -= 1
            elif direction == 'right':
                x += 1
            elif direction == 'diagonal_up_right':
                x += 1
                y += 1
            elif direction == 'diagonal_up_left':
                x -= 1
                y += 1
            elif direction == 'diagonal_down_right':
                x += 1
                y -= 1
            elif direction == 'diagonal_down_left':
                x -= 1
                y -= 1

        timestamp = datetime.now()
        response = await connect(timestamp, imei, x, y)
        yield {"timestamp": timestamp, "imei": imei, "x": x, "y": y, "response": response}
        await asyncio.sleep(random.random() * 2)


async def generate(num_users, num_actions):
    imeis = [gen_imei() for _ in range(num_users)]
    tasks = [simulate_actions(imei, num_actions) for imei in imeis]
    
    combined = stream.merge(*tasks)
    async with combined.stream() as streamer:
        async for item in streamer:
            yield item
