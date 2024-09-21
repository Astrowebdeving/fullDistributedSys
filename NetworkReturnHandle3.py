import socket
import subprocess
import time
import os

def get_client_self_name():
    return subprocess.check_output(
        "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
        shell=True, text=True
    ).strip()

client_self_name = get_client_self_name()


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 13898))
error_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    global trans1
    global trans2
    try:
   
        data, address = server_socket.recvfrom(1024)
        print(f"This here is the address: {address}")
        message = data.decode('utf-8')
        if message.startswith("T2"):
            parts = message.split(';')
            server_self_name = str(parts[2])
            time_on_reception = float(parts[4])
            curr_time = float(parts[6])
            repetition_index = int(parts[8])
            

            curr_client_time = time.time()
            with open(f"time3_{client_self_name}_{repetition_index}.txt", 'w') as f:
                f.write(str(curr_client_time))
            os.system(f"touch time3_{server_self_name}_{repetition_index}_i.txt")
            with open(f"time3_{server_self_name}_{repetition_index}_i.txt", 'w') as f:
                f.write(str(time_on_reception))
            os.system(f"touch time3_{server_self_name}_{repetition_index}_f.txt")
            with open(f"time3_{server_self_name}_{repetition_index}_f.txt", 'w') as f:
                f.write(str(curr_time))

            
            with open(f"time_curr1_{client_self_name}_{repetition_index}_{server_self_name}.txt", 'r') as f:
                initial_client_time = float(f.read().strip())
            
            time_diff = curr_time - time_on_reception
            full_diff = curr_client_time - initial_client_time
            full_add = curr_client_time + initial_client_time
            time_add = curr_time + time_on_reception
            Cristian_time = (curr_time + time_on_reception) / 2 + (full_diff) / 2
            Trans_time = (full_add - time_add) / 2
            time_delta = curr_client_time - Cristian_time 
            Error = (curr_client_time - initial_client_time - (time_diff)) / 2

            
            print("#######################")
            print(f"Using server with name: {server_self_name}")
            print(f"time_diff: {time_diff}")
            print(f"full_diff: {full_diff}")
            print(f"Cristian_time: {Cristian_time}")
            print(f"Error: {Error}")
            print(f"Trans_time: {Trans_time}")
            print(f"curr_client_time: {curr_client_time}")
            print(f"time_delta: {time_delta}")
            print("#######################")
            response_message = f"T2;x;{client_self_name};g*;{Trans_time};y;{Error}".encode('utf-8')
            ###error_socket.sendto(response_message, (address[0], 13898))
            if repetition_index == 1:
                trans1 = Trans_time
            if repetition_index == 2:
                trans2 = Trans_time
            with open(f"error_diff_{client_self_name}_{server_self_name}_{repetition_index}.txt", 'w') as f:
                f.write(str(Error))
            if repetition_index == 3:
                ###with open("output.txt", "w+") as output:
                ##subprocess.call(["python", "./script.py"], stdout=output);
                lastTrans = Trans_time
                print(f"server_self_name: {server_self_name}, trans1: {trans1}, trans2: {trans2}, lastTrans: {lastTrans}")
                subprocess.run(["python3", "Calculatting_final.py", str(server_self_name), str(trans1), str(trans2), str(lastTrans)])
        
        elif message.startswith("T1"):
            print("Pinging from the first client for some reason")
            continue
    except Exception as e:
        print(f"Error: {e}")

#server_socket.close()
