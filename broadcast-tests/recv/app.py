import socket
import sys
import json

UDP_PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    data = json.loads(data.decode("utf-8"))
    print("received message:", data, file=sys.stderr)
