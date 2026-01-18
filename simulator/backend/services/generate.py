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
    x = random.randint(X_MIN, X_MAX)
    y = random.randint(Y_MIN, Y_MAX)
    speed = random.random() * 30

    for _ in range(num_actions):
        if random.random() < 0.3:  # chance to stay at same location
            pass
        else:
            direction = random.choice(['up', 'down', 'left', 'right',
                                       'diagonal_up_right', 'diagonal_up_left',
                                       'diagonal_down_right', 'diagonal_down_left'])
            # some more random jitter
            move_amount = speed + random.random() * speed / 10
            # make speed consistent
            diag_move_amount = move_amount / math.sqrt(2)
            move_amount, diag_move_amount = int(move_amount), int(diag_move_amount)
            if direction == 'up':
                y += move_amount
            elif direction == 'down':
                y -= move_amount
            elif direction == 'left':
                x -= move_amount
            elif direction == 'right':
                x += move_amount
            elif direction == 'diagonal_up_right':
                x += diag_move_amount
                y += diag_move_amount
            elif direction == 'diagonal_up_left':
                x -= diag_move_amount
                y += diag_move_amount
            elif direction == 'diagonal_down_right':
                x += diag_move_amount
                y -= diag_move_amount
            elif direction == 'diagonal_down_left':
                x -= diag_move_amount
                y -= diag_move_amount

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
