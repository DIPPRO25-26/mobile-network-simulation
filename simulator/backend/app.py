from flask import Flask, request, jsonify
from flask_cors import CORS
from services.generate import generate
from services.replay import replay
from comms.api import connect
import os

app = Flask(__name__)

CORS(app, origins=[os.environ.get(
    "FRONTEND_URL", default="http://localhost:5002")])


@app.route('/')
def status():
    return "User Simulation Service is running."


@app.route('/generate', methods=['POST'])
def generate_users():
    data = request.get_json()

    users = data.get('users')
    actions = data.get('events')

    result = generate(users, actions)

    return jsonify(result)


@app.route('/replay', methods=['POST'])
def replay_actions():
    data = request.get_json()
    csv_path = data.get('csv_path')

    result = replay(csv_path)

    return jsonify(result)


@app.route('/connect', methods=['POST'])
def connect_endpoint():
    data = request.get_json()
    X = data.get('X')
    Y = data.get('Y')
    imei = data.get('imei')
    timestamp = data.get('timestamp')

    connect(X, Y, imei, timestamp)

    return jsonify({"status": "connect succesful", "imei": imei})


if __name__ == '__main__':
    app.run(port=10000, debug=True)
