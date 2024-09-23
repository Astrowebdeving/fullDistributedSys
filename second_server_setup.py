import socket
import subprocess
import time
import os
import threading
import configparser
from datetime import datetime

stop_threads = True
# Constants
RESPONSE_PORT = 19831
CLIENT_PORT = 19834
SERVER_PORT_1 = 19833
SERVER_PORT_2 = 19835
REPEAT_COUNT = 5
e1_thread = None
f2_thread = None
# Get the server's name from /etc/hosts
server_current_self_name = subprocess.check_output(
    "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
    shell=True, text=True
).strip()

# Load server configurations
config = configparser.ConfigParser()
config.read('config1.ini')

reception_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Set up UDP sockets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket_2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

reception_socket_1.bind(('', RESPONSE_PORT))
server_socket_1.bind(('', SERVER_PORT_1))
server_socket_2.bind(('', SERVER_PORT_2))


# Function to handle incoming E1 messages
def handle_e1_message(data, address):
    global stop_threads
    if stop_threads: return
    message = data.decode('utf-8')
    if message.endswith('\x04'):
        time_on_reception = time.time()
        message = message[:-1]  
        if message.startswith("E1"):
            parts = message.split(';')
            client_self_name = parts[2]
            current_time_received = float(parts[4])
            repetition_count = int(parts[6])

            print(repetition_count)
            with open(f"error_time_2_{client_self_name}_{repetition_count}.txt", 'w') as f:
                f.write(str(current_time_received))

            current_server_time = time.time()
##            with open(f"error_time_curr2_{server_current_self_name}_{repetition_count}_{client_self_name}.txt", 'w') as f:
##                f.write(str(current_server_time))

            response_message = f"F2;x;{server_current_self_name};g*;{time_on_reception};y;{current_server_time};z*;{repetition_count}".encode('utf-8')
            client_socket.sendto(response_message, (address[0], SERVER_PORT_2))


def listen_for_e1_messages():
    global stop_threads
    while not stop_threads:  
        try:
            data, address = server_socket_1.recvfrom(1024)
            handle_e1_message(data, address)
        except socket.timeout:
            pass  


def send_e1_messages(server_ip, sendPort):
    for i in range(REPEAT_COUNT):
        if stop_threads:  
            break
        time.sleep(0.05)
        current_time = time.time()
        message = f"E1;x;{server_current_self_name};g*;{current_time};z*;{i+1}\x04".encode('utf-8')
        client_socket.sendto(message, (server_ip, sendPort))
        # os.system(f"touch error_time_curr1_{server_current_self_name}_{i+1}_{server_ip}.txt")
        with open(f"error_time_curr1_{server_current_self_name}_{i+1}_{server_ip}.txt", 'w') as f:
            f.write(str(current_time))

def get_chronyc():

# Command to run (chronyc sources)
    command = ['chronyc', 'sources']

# Run the command and capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Access the captured output and errors
    output = result.stdout
    print(f"Chronyc error: {output}")

def handle_f2_message(data):
    global stop_threads
    if stop_threads: return 
    message = data.decode('utf-8')
    if message.startswith("F2"):
        curr_client_time = time.time()
        parts = message.split(';')
        
        prev_server_self_name = str(parts[2])
        time_on_reception = float(parts[4])
        curr_time = float(parts[6])
        repetition_index = int(parts[8])



        with open(f"error_time_curr1_{server_current_self_name}_{repetition_index}_{prev_server_self_name}.txt", 'r') as f:
            initial_client_time = float(f.read().strip())

        time_diff = curr_time - time_on_reception
        full_diff = curr_client_time - initial_client_time
        full_add = curr_client_time + initial_client_time
        time_add = curr_time + time_on_reception
        Cristian_time = (curr_time + time_on_reception) / 2 + (full_diff) / 2
        time_delta = curr_client_time - Cristian_time 
        Trans_time = (curr_client_time - initial_client_time - time_diff) / 2
        Error = (curr_client_time-curr_time -Trans_time) 
        now = datetime.now()



        formatted_now = now.strftime("%A, %B %d, %Y %I:%M %p")
        print("#######################")
        print(formatted_now)
        print(f"Index of Repetition: {repetition_index}")
        print(f"Synchronizing with server of name: {prev_server_self_name}")
        print(f"time_diff: {time_diff}")
        print(f"full_diff: {full_diff}")
        print(f"Cristian_time: {Cristian_time}")
        print(f"Error: {Error}")
        print(f"Trans_time: {Trans_time}")
        print(f"curr_client_time: {curr_client_time}")
        print(f"time_delta: {time_delta}")
        print("#######################")
        global error1, error2, error3, error4, lastError
        if repetition_index == 1:
            error1 = Error
        elif repetition_index == 2:
            error2 = Error           
        elif repetition_index == 3:
            error3 = Error               
        elif repetition_index == 4:
            error4 = Error     
        elif repetition_index == 5:
            lastError = Error
            final_error_time = (error1 + error2 + error3 + error4 + lastError) / 5
            print(f"Ending error result is {final_error_time}")
            get_chronyc()
            #with open(f"Final_error_diff_{server_current_self_name}_{prev_server_self_name}.txt", 'w') as f:
            #    f.write(str(final_error_time))
            #os.system("gcc -o time_setting_ns time_setting_ns.c")
            #command = f"sudo ./time_setting_ns {final_error_time}"
            #try:
            #    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            #    print(result.stdout)  # Output from the command
            #except subprocess.CalledProcessError as e:
            #    print(f"Error: {e.stderr}")
            send_h2_messages(prev_server_self_name)


def listen_for_f2_messages():
    global stop_threads
    while not stop_threads:  
        try:
            data, address = server_socket_2.recvfrom(1024)
            handle_f2_message(data)
        except socket.timeout:
            pass 

# Send H2 message to other servers
def send_h2_messages(origin_Server):
    for server_ip in edgelist:
        if len(edgelist) < 2:
            print("Dead End Server")
        if server_ip.strip() != origin_Server:
            print(f"current Server_IP sending to is {server_ip}")
            message = f"H2;x;{server_current_self_name}".encode('utf-8')
            client_socket.sendto(message, (server_ip.strip(), RESPONSE_PORT))

def stop_current_threads():
    global stop_threads, e1_thread, f2_thread, client_socket, server_socket_1, server_socket_2
    stop_threads = True  
    print("Stopping Threads Now")
    if e1_thread is not None:  
        e1_thread.join(timeout=0)
        e1_thread = None
    if f2_thread is not None:  
        f2_thread.join(timeout=0)
        f2_thread = None
    #server_socket_1.close()
    #server_socket_2.close()
    #client_socket.close()
    #client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #server_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #server_socket_2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #server_socket_1.bind(('', SERVER_PORT_1))
    #server_socket_2.bind(('', SERVER_PORT_2))
if __name__ == "__main__":
    edgelist = config['edgelist']['edgelist'].split(',')
    while True:
        data, address = reception_socket_1.recvfrom(1024)
        message = data.decode('utf-8')
        if message.startswith("H2"):
            if stop_threads == False: 
                stop_current_threads()
            parts = message.split(';')
            originating_server_name = parts[2]
            stop_threads = False 
            
            e1_thread = threading.Thread(target=listen_for_e1_messages)
            f2_thread = threading.Thread(target=listen_for_f2_messages)

            e1_thread.start()
            f2_thread.start()
            send_e1_messages(originating_server_name, SERVER_PORT_1)

