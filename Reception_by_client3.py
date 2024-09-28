import socket
import os
import configparser
import struct

# Buffer size for UDP
buffer_size = 1024

# UDP socket setup to receive on port 30139
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 30139))
print("Listening for incoming config files on port 30139...")

# Step 1: Receive the file size
packed_file_size, addr = sock.recvfrom(8)
file_size = struct.unpack("!Q", packed_file_size)[0]
print(f"Expected file size: {file_size} bytes from {addr}")

# Step 2: Receive the compressed file
compressed_file = "config_received1.tar.gz"
bytes_received = 0

with open(compressed_file, "wb") as f:
    while bytes_received < file_size:
        data, _ = sock.recvfrom(buffer_size)
        if not data:
            break
        f.write(data)
        bytes_received += len(data)

print(f"Received compressed file from {addr}, saving as {compressed_file}, total bytes received: {bytes_received}")

# Step 3: Decompress the received file
os.system(f"tar -xzvf {compressed_file}")

# Decompressed file is named config1.ini
config_received = configparser.ConfigParser()
config_received.read("config1.ini")

# Local config file
config_local = configparser.ConfigParser()
config_local.read("config1.ini")

# Merge the edgelist
received_edgelist = config_received.get('edgelist', 'servers', fallback="").split(',')
local_edgelist = config_local.get('edgelist', 'servers', fallback="").split(',')

# Merge and update the edgelist
merged_edgelist = set(local_edgelist + received_edgelist)
config_local.set('edgelist', 'servers', ','.join(merged_edgelist))

with open('config1.ini', 'w') as configfile:
    config_local.write(configfile)

print("Merged edgelist saved to config1.ini.")
