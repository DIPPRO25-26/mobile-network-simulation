from comms.api import connect
import csv
import time


def replay(csv_path):
    imei = csv_path.split('/')[-1].split('.')[0]

    with open(csv_path, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            timestamp = row[0]
            x = row[1]
            y = row[2]
            connect(int(x), int(y), imei, timestamp)
            time.sleep(1)

    return {"status": "replay completed", "imei": imei}
