import socket
import subprocess
import time
import configparser

# Get client self name
client_self_name = subprocess.check_output(
    "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
    shell=True, text=True
).strip()

config = configparser.ConfigParser()


config.read('config.ini')

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ("manager0", 22834)

        # Get current time
current_time = time.time()

        # Create message with EOT marker
message = f"T1;x;{client_self_name};g*;{current_time}\x04".encode('utf-8')  # \x04 is the EOT character

        # Send message to server
client_socket.sendto(message, server_address)

        # Write current time to file
with open(f"man_server_1_time{client_self_name}.txt", 'w') as f:
            f.write(str(current_time))

client_socket.close()
