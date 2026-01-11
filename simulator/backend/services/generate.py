from datetime import datetime
from comms.api import gen_imei, connect
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import X_MAX, X_MIN, Y_MAX, Y_MIN
import random
import time
import csv


def simulate_actions(imei, num_actions):
    x = random.randint(X_MIN, X_MAX)
    y = random.randint(Y_MIN, Y_MAX)

    csv_path = f'csv_logs/{imei}.csv'

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

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        connect(x, y, imei, timestamp)
        with open(csv_path, "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, x, y,])
        time.sleep(1)

    return csv_path


def generate(num_users, num_actions):
    user_csv_logs = []
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        imeis = [gen_imei() for _ in range(num_users)]
        futures = {executor.submit(
            simulate_actions, imei, num_actions): imei for imei in imeis}
        for future in as_completed(futures):
            user_csv_logs.append(future.result())

    return user_csv_logs
