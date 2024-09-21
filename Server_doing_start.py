import socket
import os

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 22834))

response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    try:
        data, address = server_socket.recvfrom(1024)
        message = data.decode('utf-8')
        if message.endswith('\x04'):
            parts = message.split(';')
            if parts[2] == "Startnow":
                os.system(f"python3 Server1_ping.py")
    except Exception as e:
        print(f"Error: {e}")