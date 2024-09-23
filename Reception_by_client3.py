import socket
import os
import configparser
import subprocess

# Buffer size for UDP
buffer_size = 1024

# UDP socket setup to receive on port 30139
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 30139))
print("Listening for incoming config files on port 30139...")

# Receive the compressed file
compressed_file = "config_received1.tar.gz"
with open(compressed_file, "wb") as f:
    while True:
        data, addr = sock.recvfrom(buffer_size)
        if not data:
            break
        f.write(data)
print(f"Received compressed file from {addr}, saving as {compressed_file}")

# Decompress the received file
os.system(f"tar -xzvf {compressed_file}")

# Decompressed file is named config_received1.ini
config_received = configparser.ConfigParser()
config_received.read("config_received1.ini")

# Local config file
config_local = configparser.ConfigParser()
config_local.read("config1.ini")

# Check and add the [edgelist] section if not present
if 'edgelist' not in config_local.sections():
    config_local.add_section('edgelist')

# Append edgelist from the received config
received_edgelist = config_received.get('edgelist', 'servers', fallback="").split(',')
local_edgelist = config_local.get('edgelist', 'servers', fallback="").split(',')

# Merge the two edgelists
merged_edgelist = set(local_edgelist + received_edgelist)

# Save the updated edgelist back to config1.ini
config_local.set('edgelist', 'servers', ','.join(merged_edgelist))

with open('config1.ini', 'w') as configfile:
    config_local.write(configfile)

print("Merged edgelist saved to config1.ini.")
