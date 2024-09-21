import socket
import subprocess
import time


def get_server_self_name():
    return subprocess.check_output(
        "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
        shell=True, text=True
    ).strip()

server_self_name = get_server_self_name()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 22834))

response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    try:
        data, address = server_socket.recvfrom(1024)
        message = data.decode('utf-8')

        
        if message.endswith('\x04'):
            message = message[:-1]  

            if message.startswith("T1"):
                time_on_reception = time.time()
                parts = message.split(';')
                client_self_name = parts[2]
                current_time_received = float(parts[4])

                with open(f"man_server_1_time{client_self_name}.txt", 'w') as f:
                    f.write(str(current_time_received))
                current_server_time = time.time()
                with open(f"man_server_3_time{server_self_name}.txt", 'w') as f:
                    f.write(str(current_server_time))
                
               
                response_message = f"T2;x;{server_self_name};g*;{time_on_reception};y;{current_server_time}".encode('utf-8')
                response_socket.sendto(response_message, (address[0], 23898))
    except Exception as e:
        print(f"Error: {e}")
