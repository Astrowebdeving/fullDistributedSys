import socket
import threading
import os
import configparser
import struct
import ast

# Server setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("", 29374))
print("UDP server is listening on port 29374...")

buffer_size = 1024

# Read the network list
config_network = configparser.ConfigParser()
config_network.read('config_network.ini')
networklist = config_network.get('networklist', 'servers', fallback="").split(',')

received_clients = []  # Keep track of clients we've received files from

# Step 1: Merging logic for the combined configuration
def merge_configs(received_config_file, received_server_name):
    # Load the received config file
    received_config = configparser.ConfigParser()
    received_config.read(received_config_file)

    # Load the combined config
    config_combined = configparser.ConfigParser()
    config_combined.read('config_combined.ini')

    # Merge the received config into the combined config
    if received_server_name in received_config.sections():
        if received_server_name not in config_combined.sections():
            config_combined.add_section(received_server_name)
        for key, value in received_config.items(received_server_name):
            config_combined.set(received_server_name, key, value)

    # Save the updated combined config
    with open('config_combined.ini', 'w') as combined_file:
        config_combined.write(combined_file)

    print(f"Appended section [{received_server_name}] to config_combined.ini")


# Step 2: Update the merged network using the lowest transmission time
def update_merged_network():
    """
    This function updates the [merged_network] section in config_combined.ini by finding
    the lowest trans_time for each server in the networklist.
    """
    merged_network = {}
    config_combined = configparser.ConfigParser()
    config_combined.read('config_combined.ini')

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

    print("Merged network updated with the lowest transmission times for each server.")


# Step 3: Update the server edgelists based on the merged network
def update_server_edgelists():
    """
    For each server_component in networklist, search the merged_network for both origin_server
    and server_name values that match the server_component. If found, append the corresponding
    dictionary to the edgelist in config1_{server_component}.ini.
    """
    config_combined = configparser.ConfigParser()
    config_combined.read('config_combined.ini')

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
            if entry["origin_server"] == server_component or entry["server_name"] == server_component:
                if entry["server_name"] not in edgelist:
                    edgelist.append(entry["server_name"])

        # Update the edgelist in the server config file
        config_server.set('edgelist', 'servers', ','.join(edgelist))

        # Save the updated config file
        with open(server_config_file, 'w') as server_file:
            config_server.write(server_file)

        print(f"Updated edgelist for {server_component} in {server_config_file}")


# Step 4: Compress and send the edgelist config file back to the clients
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

    print(f"Config file for {server_component} sent.")


# Step 5: Handle the reception of client files and initiate the merging process
def handle_client(client_addr):
    try:
        # Step 1: Receive the file size
        print(f"Handling client {client_addr}")
        packed_file_size, _ = server_socket.recvfrom(8)
        file_size = struct.unpack("!Q", packed_file_size)[0]
        print(f"Expected file size: {file_size} bytes")

        # Step 2: Receive the file in chunks
        compressed_file = f"config_received_{client_addr}.tar.gz"
        bytes_received = 0
        
        with open(compressed_file, "wb") as f:
            while bytes_received < file_size:
                data, addr = server_socket.recvfrom(buffer_size)
                if not data:
                    break
                f.write(data)
                bytes_received += len(data)
        
        print(f"Received file '{compressed_file}' from {client_addr}, total bytes received: {bytes_received}")
        
        # Step 3: Decompress the tar.gz file
        os.system(f"tar -xzvf {compressed_file}")
        print(f"Decompressed file from {client_addr}")

        # Get server name from client_addr and merge
        server_name = f"client_{client_addr[0]}"
        merge_configs(f"config1_{server_name}.ini", server_name)

        # Keep track of clients
        if server_name not in received_clients:
            received_clients.append(server_name)

        # Step 4: Create individual config files with edgelist for all clients
        update_merged_network()
        update_server_edgelists()

        # Step 5: Send the updated edgelist files back to the clients
        for client in received_clients:
            send_compressed_file_send(client)

    except Exception as e:
        print(f"Error handling client {client_addr}: {e}")


# Step 6: Start the server and listen for incoming client connections
def start_server():
    while True:
        # Use threading to handle multiple clients
        data, client_addr = server_socket.recvfrom(buffer_size)
        threading.Thread(target=handle_client, args=(client_addr,)).start()

start_server()
