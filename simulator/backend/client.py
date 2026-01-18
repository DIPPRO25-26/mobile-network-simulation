import requests as r
import json

url = "http://127.0.0.1:5002/generate"
req={"users":1, "events":20}
with r.post(url, json=req, stream=True) as resp:
    for line in resp.iter_lines():
        data = json.loads(line)
        print(data["timestamp"], data["imei"], data["x"], data["y"])
