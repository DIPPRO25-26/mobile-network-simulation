from comms.api import connect, send_keep_alive, clear
import asyncio

async def replay(events):
    await clear()
    last_ts = events[0][0]
    should_connect = True
    for timestamp, imei, x, y in events:
        await asyncio.sleep((timestamp - last_ts).total_seconds())

        if (should_connect):
            response = await connect(timestamp, imei, x, y)
            inner_response = response.get("response", {})
            data = inner_response.get("data", {})
            if data.get("action") == "disconnect":
                should_connect = True
            else:
                should_connect = False
        else:
            response = await send_keep_alive(timestamp, imei, x, y)
            inner_response = response.get("response", {})
            data = inner_response.get("data", {})
            if (data.get("action") == "handover"):
                should_connect = True
            if (data.get("action") == "disconnect"):
                print(f"User {imei} disconnected. --------------------------------------")
                should_connect = True
                
        yield {"timestamp": timestamp, "imei": imei, "x": x, "y": y, "response": response}
        last_ts = timestamp

