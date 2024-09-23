import socket
import configparser
import subprocess
import time
import threading

SERVER_PORT_1 = 19833
SERVER_PORT_2 = 19835
REPEAT_COUNT = 5

# Set up UDP sockets
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket_2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


server_socket_1.bind(('', SERVER_PORT_1))
server_socket_2.bind(('', SERVER_PORT_2))


# Get the current machine's name
def get_current_self_name():
    return subprocess.check_output(
        "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
        shell=True, text=True
    ).strip()
server_current_self_name = get_current_self_name()
# Function to send UDP messages
def send_udp_message(ip, message, port=19831):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.sendto(message.encode('utf-8'), (ip, port))
    udp_socket.close()

# Read the config1.ini file and send messages based on edgelist
def read_config_and_send_messages(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    # Get the current machine name
    current_self_name = get_current_self_name()
    print(f"Current machine: {current_self_name}")

    if 'edgelist' in config:
        # Get the machines from the edgelist entry
        edgelist = config['edgelist']['edgelist']
        machines = [name.strip() for name in edgelist.split(',')]

        # Loop over each machine in the list
        for machine_name in machines:
            # Resolve IP address from /etc/hosts
            try:
                machine_ip = subprocess.check_output(
                    f"getent hosts {machine_name} | awk '{{print $1}}'",
                    shell=True, text=True
                ).strip()

                if machine_ip:
                    message = f"H2;x;{current_self_name}"
                    print(f"Sending message to {machine_name} ({machine_ip})")
                    send_udp_message(machine_ip, message)
                else:
                    print(f"Could not resolve IP for {machine_name}")
            except subprocess.CalledProcessError as e:
                print(f"Error resolving IP for {machine_name}: {e}")
    else:
        print("No [edgelist] section found in the config file")

# Read the config2.ini file and create config_tree.ini grouped by origin_server
def create_grouped_config_tree(config2_file, output_file):
    config2 = configparser.ConfigParser()
    config2.read(config2_file)

    grouped_servers = {}

    # Read the [groupingINFO] section from config2.ini
    if 'groupingINFO' in config2:
        for server, info in config2['groupingINFO'].items():
            server_data = eval(info)  # Convert string representation to a dictionary
            origin_server = server_data['origin_server']
            if origin_server not in grouped_servers:
                grouped_servers[origin_server] = []
            grouped_servers[origin_server].append({server: server_data})

    # Write to a new config_tree.ini
    config_tree = configparser.ConfigParser()

    # Add an [EdgeTree] section
    config_tree.add_section('EdgeTree')

    # Group and write the data by origin_server
    edge_count = 1
    for origin_server, servers in grouped_servers.items():
        section_name = f'{origin_server}_list'
        config_tree.add_section(section_name)

        for server_entry in servers:
            for server, server_data in server_entry.items():
                edge_key = f'Edge{edge_count}'
                config_tree[section_name][edge_key] = str(server_data)
                edge_count += 1

    # Write to the output file
    with open(output_file, 'w') as configfile:
        config_tree.write(configfile)
    print(f"Created grouped config tree: {output_file}")

def handle_e1_message(data, address):
    message = data.decode('utf-8')

    if message.endswith('\x04'):
        message = message[:-1]  
        if message.startswith("E1"):
            time_on_reception = time.time()
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
    while True:
        data, address = server_socket_1.recvfrom(1024)
        handle_e1_message(data, address)


# Main
if __name__ == '__main__':
    # Path to your config files
    config_file1 = 'config1.ini'
    config_file2 = 'config2.ini'
    output_file = 'config_tree.ini'
    
    # Get the current machine name
    current_self_name = get_current_self_name()

    # Read config1.ini and send messages
    read_config_and_send_messages(config_file1)
    e1_thread = threading.Thread(target=listen_for_e1_messages)
    e1_thread.start()


    print(f"Processing config2.ini and creating config_tree.ini ")
    command = ['chronyc', 'sources']

# Run the command and capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Access the captured output and errors
    output = result.stdout
    print(f"The Error with chronyc is {output}")
    try: 
        create_grouped_config_tree(config_file2, output_file)
    except Exception as e:
        print(f"Error seen as: {e}")

