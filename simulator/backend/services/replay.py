from comms.api import connect, send_keep_alive
import asyncio

async def replay(events):
    last_ts = events[0][0]
    should_connect = True
    for timestamp, imei, x, y in events:
        await asyncio.sleep((timestamp - last_ts).total_seconds())

        if (should_connect):
            response = await connect(timestamp, imei, x, y)
            should_connect = False
        else:
            response = await send_keep_alive(x, y, imei, timestamp)
            if (response.get("action") == "handover"):
                should_connect = True
                
        yield {"timestamp": timestamp, "imei": imei, "x": x, "y": y, "response": response}
        last_ts = timestamp

