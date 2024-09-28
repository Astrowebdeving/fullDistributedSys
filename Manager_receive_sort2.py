import socket
import subprocess
import os
import configparser
import ast  # To safely parse dictionary strings from config
import datetime

# Get the server's machine name (should be manager0)
machine_name = subprocess.check_output(
    "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep -w $ip | awk '{print $2}'",
    shell=True, text=True
).strip()

# Ensure this is the correct machine
if machine_name != "manager0":
    raise RuntimeError("This script should only run on manager0")

# UDP server setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("", 29374))
print("UDP server is listening on port 29374...")

# Buffer size
buffer_size = 1024

# Load networklist from config_network.ini
config_network = configparser.ConfigParser()
config_network.read('config_network.ini')
networklist = config_network.get('networklist', 'servers', fallback="").split(',')

import subprocess

def get_machine_from_ip(client_ip):
    # Use single quotes around the shell command to avoid conflicts with double quotes in the command
    command = f"client_name=$(grep -w '{client_ip}' /etc/hosts | awk '{{print $2}}'); echo $client_name"
    
    try:
        client_name = subprocess.check_output(command, shell=True, text=True).strip()
        return client_name
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return None

# Create a config parser for appending to confi
# g_combined.ini
config_combined = configparser.ConfigParser()

def update_merged_network():
    """
    This function updates the [merged_network] section in config_combined.ini by finding
    the lowest trans_time for each server in the networklist.
    """
    merged_network = {}

    # Iterate over all server components in networklist
    for server_component in networklist:
        lowest_trans_time = float('inf')
        best_entry = None

        # Iterate through all sections in config_combined
        for section in config_combined.sections():
            # Look for the server_component in the dictionary values in each section
            for key, value in config_combined.items(section):
                entry = ast.literal_eval(value)  # Convert the string back to a dictionary

                # If the server_name matches the server_component, check its trans_time
                if entry["server_name"] == server_component:
                    trans_time = float(entry["trans_time"])
                    if trans_time < lowest_trans_time:
                        lowest_trans_time = trans_time
                        best_entry = entry

        # Add the best entry to the merged_network if found
        if best_entry:
            merged_network[server_component] = best_entry

    # Add or update the [merged_network] section in config_combined
    if 'merged_network' not in config_combined.sections():
        config_combined.add_section('merged_network')

    for server_component, entry in merged_network.items():
        config_combined.set('merged_network', server_component, str(entry))

    # Save the updated config_combined.ini
    with open('config_combined.ini', 'w') as combined_file:
        config_combined.write(combined_file)

def update_server_edgelists():
    """
    For each server_component in networklist, search the merged_network for both origin_server
    and server_name values that match the server_component. If found, append the corresponding
    dictionary to the edgelist in config1_{server_component}.ini.
    """
    for server_component in networklist:
        # Open or create config1_{server_component}.ini
        config_server = configparser.ConfigParser()
        server_config_file = f"config1_{server_component}.ini"
        if os.path.exists(server_config_file):
            config_server.read(server_config_file)
        else:
            config_server.add_section('edgelist')

        # Search through merged_network for matches to origin_server and server_name
        edgelist = config_server.get('edgelist', 'servers', fallback="").split(',')
        for key, value in config_combined.items('merged_network'):
            entry = ast.literal_eval(value)

            # If both origin_server and server_name match, add to edgelist
            if entry["origin_server"] == server_component and entry["server_name"] == server_component:
                if entry["server_name"] not in edgelist:
                    edgelist.append(entry["server_name"])

        # Update the edgelist in the server config file
        config_server.set('edgelist', 'servers', ','.join(edgelist))

        # Save the updated config file
        with open(server_config_file, 'w') as server_file:
            config_server.write(server_file)

        print(f"Updated edgelist for {server_component} in {server_config_file}")
def send_compressed_file_send(server_component):
    compressed_file = f"config1_{server_component}.tar.gz"
    config_file = f"config1_{server_component}.ini"

    # Compress the config1_{server_component}.ini file
    os.system(f"tar -czvf {compressed_file} {config_file}")

    # Server address
    server_address = (server_component, 30139)

    # Send the compressed file over UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        with open(compressed_file, "rb") as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                sock.sendto(data, server_address)
        print(f"Compressed config file '{compressed_file}' sent to {server_component} on port 30139")

    finally:
        sock.close()


    print("All config files sent.")

while True:
    try:
        # Step 1: Receive the header
        data, addr = server_socket.recvfrom(buffer_size)
        message = data.decode('utf-8').strip()
        client_recv_ip = addr[0]
        received_server_name = get_machine_from_ip(client_recv_ip)

        # Step 2: Receive the compressed file
        compressed_file = f"config1_{received_server_name}.tar.gz"
        with open(compressed_file, "wb") as f:
            print(f"Receiving compressed file for {received_server_name}...")
            while True:
                try:
                # Receive binary data for the file
                    data, addr = server_socket.recvfrom(buffer_size)
                    if not data:
                        break
                    f.write(data)
                except Exception as e:
                    print(f"Error in server loop: {e}")


        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Print the client's IP, port, and the current date
        print(f"Received message from IP: {client_recv_ip}, Port: 29374, Date: {current_time}")

        # Step 3: Decompress the tar.gz file
        os.system(f"tar -xzvf {compressed_file}")
        print(f"Decompressed file for {received_server_name}")

        # Step 4: Process the config file and merge with combined config
        config_file_name = f"config1_{received_server_name}.ini"
        received_config = configparser.ConfigParser()
        received_config.read(config_file_name)

        config_combined.read('config_combined.ini')
        if received_server_name in received_config.sections():
            if received_server_name not in config_combined.sections():
                config_combined.add_section(received_server_name)
            for key, value in received_config.items(received_server_name):
                config_combined.set(received_server_name, key, value)

        # Save the updated config_combined.ini
        with open('config_combined.ini', 'w') as combined_file:
            config_combined.write(combined_file)

        print(f"Appended section [{received_server_name}] to config_combined.ini")

        # Update merged network and edgelists
        update_merged_network()
        update_server_edgelists()

        # Send the updated files to the network
        for server_component in networklist:
            if os.path.exists(f"config1_{server_component}.ini"):
                send_compressed_file_send(server_component)
            else:
                print(f"Config file for {server_component} does not exist.")

    except UnicodeDecodeError:
        print("Failed to decode the header, skipping this packet.")
    except Exception as e:
        print(f"Error: {e}")

    # No socket closing here - server will continue to listen for requests