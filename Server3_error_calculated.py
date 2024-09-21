import socket
import subprocess
import time

# Get client self name
def get_client_self_name():
    return subprocess.check_output(
        "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
        shell=True, text=True
    ).strip()

client_self_name = get_client_self_name()

# Create UDP socket for receiving response
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('', 23898))
error_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    try:
        # Receive response with a buffer size of 1024
        data, address = server_socket.recvfrom(1024)
        message = data.decode('utf-8')

        if message.startswith("T2"):
            parts = message.split(';')
            time_on_reception = float(parts[4])
            curr_time = float(parts[6])
            
            # Write times to files
            curr_client_time = time.time()
            with open(f"man_server_4_time{client_self_name}.txt", 'w') as f:
                f.write(str(curr_client_time))
            server_self_name = address[0]  # Assuming server_self_name can be derived from the response address
            with open(f"man_server_2_time{server_self_name}_i.txt", 'w') as f:
                f.write(str(time_on_reception))
            with open(f"man_server_3_time{server_self_name}_f.txt", 'w') as f:
                f.write(str(curr_time))

            # Read initial client time
            with open(f"man_server_1_time{client_self_name}.txt", 'r') as f:
                initial_client_time = float(f.read().strip())

            # Calculate times
            time_diff = curr_time - time_on_reception
            full_diff = curr_client_time - initial_client_time
            full_add = curr_client_time + initial_client_time
            time_add = curr_time + time_on_reception
            Cristian_time = (curr_time + time_on_reception) / 2 + (full_diff) / 2
            Trans_time = (full_add - time_add) / 2
            time_delta = curr_client_time - Cristian_time 
            Error = (curr_client_time - initial_client_time - (time_diff)) / 2

            # Print results
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
            print(f"The error between the manager and server is: {Error}")
            ###os.system("gcc -o time_setting_ns time_setting_ns.c")
            ###command = f"sudo ./time_setting_ns {Error}"
            ###try:
             ###  result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
              ##  print(result.stdout)  # Output from the command
            ##except subprocess.CalledProcessError as e:
              ##  print(f"Error: {e.stderr}")
            ###os.system("python3 first_server_setup.py")
    except Exception as e:
        print(f"Error: {e}")

#server_socket.close()
