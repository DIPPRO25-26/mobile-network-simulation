from comms.api import connect
import asyncio

async def replay(events):
    last_ts = events[0][0]
    for timestamp, imei, x, y in events:
        await asyncio.sleep((timestamp - last_ts).total_seconds())
        response = await connect(timestamp, imei, x, y)
        yield {"timestamp": timestamp, "imei": imei, "x": x, "y": y, "response": response}
        last_ts = timestamp

