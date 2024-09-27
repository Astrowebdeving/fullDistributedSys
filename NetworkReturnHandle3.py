import socket
import subprocess
import time
import os
import multiprocessing
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log', mode='a'), logging.StreamHandler()]
)

# Function to get the client's self name
def get_client_self_name():
    try:
        return subprocess.check_output(
            "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep -w $ip | awk '{print $2}'",
            shell=True, text=True
        ).strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get client self name: {e}")
        return None

client_self_name = get_client_self_name()
print(client_self_name)
if not client_self_name:
    logging.error("Client self name could not be determined. Exiting.")
    exit(1)

# Shared manager dict to store transmission times for each server_self_name
manager = multiprocessing.Manager()
## = manager.dict()

# Function to handle incoming messages and process transmission times
def handle_message(data, address):
    ## add back , shared_state
    try:
        message = data.decode('utf-8')
        if message.startswith("T2"):
            parts = message.split(';')
            if len(parts) < 5:
                logging.warning(f"Malformed message received: {message}")
                return
            
            server_self_name = str(parts[2])
            try:
                repetition_index = int(parts[4])
            except ValueError:
                logging.warning(f"Invalid repetition index: {parts[4]} in message {message}")
                return
            
            curr_client_time = time.time()

            # Try writing the current client time to a file
            try:
                with open(f"time3_{client_self_name}_{repetition_index}.txt", 'w') as f:
                    f.write(str(curr_client_time))
            except IOError as e:
                logging.error(f"Failed to write to file for repetition {repetition_index}: {e}")
                return

            # Try reading the initial client time from the file
            try:
                with open(f"time_curr1_{client_self_name}_{repetition_index}_{server_self_name}.txt", 'r') as f:
                    initial_client_time = float(f.read().strip())
            except FileNotFoundError:
                logging.error(f"Initial client time file not found for {client_self_name}, repetition {repetition_index}")
                return
            except ValueError:
                logging.error(f"Invalid data in initial client time file for {client_self_name}, repetition {repetition_index}")
                return

            # Calculate transmission time
            Trans_time = (curr_client_time - initial_client_time) / 2
            logging.info(f"Processing for server: {server_self_name}, repetition: {repetition_index}, Trans_time: {Trans_time}")
            #logging.info(f"Shared State is: {shared_state}")
            # Initialize the state for the server if it doesn't exist
# #           if server_self_name not in shared_state:
# #               shared_state[server_self_name] = manager.dict()
            
            logging.info(f"Repetition index for {server_self_name} is {repetition_index}")
 # #          if repetition_index == 1:
   #  #           shared_state[server_self_name]['trans1'] = Trans_time
            logging.info(f"Repetition index 1 is found for {server_self_name}")
             #   logging.info(f"Shared State inside repindex 1 is: {shared_state}")
#            elif repetition_index == 2:
#                shared_state[server_self_name]['trans2'] = Trans_time
#                logging.info(f"Repetition index 2 is found for {server_self_name}")
             #   logging.info(f"Shared State inside repindex 2 is: {shared_state}")
#            elif repetition_index == 3:
#                shared_state[server_self_name]['lastTrans'] = Trans_time
#                logging.info(f"Repetition index 3 is found for {server_self_name}")
             #   logging.info(f"Shared State inside repindex 3 is: {shared_state}")

     #  #     logging.info(shared_state[server_self_name]['trans1'])
            # ,shared_state[server_self_name]['trans2'],shared_state[server_self_name]['lastTrans']
      #  #    logging.info(shared_state)
            # Check if all three transmissions (trans1, trans2, lastTrans) are available
       ##     if (shared_state[server_self_name]['trans1'] is not None):
    #  and shared_state[server_self_name]['trans2'] is not None and shared_state[server_self_name]['lastTrans'] is not None            
        ##        trans1 = shared_state[server_self_name]['trans1']
           ##     logging.info(shared_state[server_self_name]['trans1'])
               # trans2 = shared_state[server_self_name]['trans2']
               # logging.info(shared_state[server_self_name]['trans2'])
               # lastTrans = shared_state[server_self_name]['lastTrans']
               # logging.info(shared_state[server_self_name]['lastTrans'])
            trans1 = Trans_time
            if True:
                logging.info(f"Ready to run Calculatting_final.py for server {server_self_name} with trans1: {trans1}")

                # Call the subprocess to run Calculatting_final.py; , trans2: {trans2}, lastTrans: {lastTrans}
                try:
                    subprocess.run(["python3", "Calculatting_final.py", server_self_name, str(trans1)], check=True, timeout=12)
                    # , str(trans2), str(lastTrans)
                    logging.info(f"Calculatting_final.py executed successfully for server {server_self_name}")

                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to execute Calculatting_final.py for {server_self_name}: {e}")
                    return
                # Reset the state for the server once processed
   #             shared_state[server_self_name] = {'trans1': None}
                # , 'trans2': None, 'lastTrans': None
        elif message.startswith("T1"):
            logging.info("Received a ping (T1) message from the client.")
            return
        
    except Exception as e:
        logging.error(f"Error while processing message: {e}")

# Function to start the server and handle messages concurrently using multiprocessing
def start_server():
    ## add back shared server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 13898))

    while True:
        try:
            # Receive data and client address
            data, address = server_socket.recvfrom(1024)
            logging.info(f"Received message from {address}")

            # Process the message in a new process
            multiprocessing.Process(target=handle_message, args=(data, address)).start()
            ## add back shared_state

        except Exception as e:
            logging.error(f"Error in server loop: {e}")

# Start the server with shared state
if __name__ == '__main__':
    ##add back shared_state
    start_server()
