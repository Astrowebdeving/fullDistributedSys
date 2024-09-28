import socket
import subprocess
import os

# Get the client's self name (client_name)
client_name = subprocess.check_output(
    "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep -w $ip | awk '{print $2}'",
    shell=True, text=True
).strip()

# Server address
server_address = ("manager0", 29374)

# Compress config1.ini using tar
compressed_file = f"config1_{client_name}.tar.gz"
os.system(f"tar -czvf {compressed_file} config1.ini")

# Create the header

# Send the header and compressed file over UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Send the compressed config1.ini file (this must be sent as binary)
    print("Sending File")
    with open(compressed_file, "rb") as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sock.sendto(data, server_address)
    print(f"Compressed config file '{compressed_file}' sent to {server_address}")

finally:
    sock.close()
