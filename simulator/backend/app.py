from quart import Quart, request, make_response, jsonify
from quart_cors import cors
from services.generate import generate
from services.replay import replay
from comms.api import connect
import os, csv, json
from datetime import datetime
from io import TextIOWrapper

app = Quart(__name__)

app = cors(app, allow_origin={os.environ.get(
    "FRONTEND_URL", default="http://localhost:5002")})


@app.route('/')
async def status():
    return "User Simulation Service is running."


@app.route('/generate', methods=['post'])
async def generate_users():
    data = await request.get_json()

    users = data.get('users')
    actions = data.get('events')

    async def generate_bridge(users, actions):
        async for line in generate(users, actions):
            line["timestamp"] = line["timestamp"].isoformat()
            yield json.dumps(line) + "\n"

    response = await make_response(generate_bridge(users, actions), {"content-type": "text/event-stream"})
    response.timeout = None

    return response

@app.route('/replay', methods=['POST'])
async def replay_actions():
    files = await request.files
    if 'file' not in files:
        return "No file part", 400
    f = files['file']
    if f.filename == '':
        return "No selected file", 400

    f_wrapper = TextIOWrapper(f.stream, encoding="utf-8")
    csv_reader = csv.DictReader(f_wrapper)
    events = [(datetime.fromisoformat(i["timestamp"]), i["imei"], int(i["x"]), int(i["y"])) for i in csv_reader]

    async def replay_bridge(events):
        async for line in replay(events):
            line["timestamp"] = line["timestamp"].isoformat()
            yield json.dumps(line) + "\n"

    response = await make_response(replay_bridge(events), {"Content-Type": "text/event-stream"})
    response.timeout = None

    return response

@app.route('/connect', methods=['POST'])
async def connect_endpoint():
    data = await request.get_json()
    x = data.get('x')
    y = data.get('y')
    imei = data.get('imei')
    timestamp = datetime.fromisoformat(data.get('timestamp'))

    response = await connect(timestamp, imei, x, y)
    return jsonify({"timestamp": timestamp.isoformat(), "imei": imei, "x": x, "y": y, "response": response})
