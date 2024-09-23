import socket
import subprocess
import os

# Get the client's self name (client_name)
client_name = subprocess.check_output(
    "ip=$(hostname -I | awk '{print $1}')\ncat /etc/hosts | grep $ip | awk '{print $2}'",
    shell=True, text=True
).strip()

# Server address
server_address = ("manager0", 29374)

# Compress config1.ini using tar
compressed_file = f"config1_{client_name}.tar.gz"
os.system(f"tar -czvf {compressed_file} config1.ini")

# Create the header
header = f"FP1;x;{client_name};b;"

# Send the header and compressed file over UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Send the header first
    sock.sendto(header.encode('utf-8'), server_address)
    print(f"Header sent: {header}")
    
    # Send the compressed config1.ini file
    with open(compressed_file, "rb") as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sock.sendto(data, server_address)
    print(f"Compressed config file '{compressed_file}' sent to {server_address}")

finally:
    sock.close()
