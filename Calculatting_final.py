import socket
import subprocess
import time
import sys
import configparser
import os
import fcntl  # For file locking

# Open the log file in append mode
log_file = open('app2.log', 'a')

# Redirect stdout and stderr to log file
sys.stdout = log_file
sys.stderr = log_file

config = configparser.ConfigParser()
config.read('config1.ini')

# Function to get the client's self name
def get_client_self_name():
    try:
        return subprocess.check_output(
            "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep -w $ip | awk '{print $2}'",
            shell=True, text=True
        ).strip()
    except Exception as e:
        print(f"Error in getting client self name: {e}")
        sys.exit(1)

client_self_name = get_client_self_name()
server_name = sys.argv[1]
final_trans_time = float(sys.argv[2])
#trans_time1 = float(sys.argv[2])
#trans_time2 = float(sys.argv[3])
#trans_time3 = float(sys.argv[4])
#final_trans_time = (trans_time1 + trans_time2 + trans_time3) / 3

# Ensure the client self name exists in the config

if client_self_name not in config:
    config[client_self_name] = {}
    
server_info_str = f'{{ "server_name": "{server_name}", "trans_time": "{final_trans_time}" }}'

# Function to safely write to the config file using file locking
def safe_write_config(config, client_self_name, server_name, server_info_str):
    try:
        # Open the file in read and write mode ('r+')
        config.read('config1.ini')
        with open('config1.ini', 'r+') as configfile:
            fcntl.flock(configfile, fcntl.LOCK_EX)  # Acquire exclusive lock
            config.read_file(configfile)  # Read the latest version of the file
            # Modify the in-memory config object
            config[client_self_name][server_name] = server_info_str
            
            # Truncate the file before writing the updated config
            configfile.seek(0)  # Move to the beginning of the file
            configfile.truncate()  # Clear the file contents
            config.write(configfile)  # Write the updated config
            fcntl.flock(configfile, fcntl.LOCK_UN)  # Release the lock
            
        print(f"Successfully wrote server '{server_name}' info to config.")
    except Exception as e:
        print(f"Error while writing to config: {e}")

# Function to check if all servers have been processed and run the next step
def check_servers_and_run(config, client_self_name, hostlist):
    try:
        if client_self_name not in config:
            print(f"{client_self_name} not found in config.")
            return

        server_entries = len(config[client_self_name])
        expected_server_count = len(hostlist) - 1

        print(f"Found {server_entries} server entries for {client_self_name}. Expected: {expected_server_count}")

        if server_entries == expected_server_count:
            print(f"Server count matches {expected_server_count}. Running Clients_send_pinginfo1.py...")
            with open(f"completed_trans_calculation.txt", 'w') as f:
                f.write("True")
            time.sleep(1)
            try:
                os.system("python3 Clients_send_pinginfo1.py")
            except Exception as e:
                print(f"Error in server loop: {e}")

        else:
            print(f"Server count does not match {expected_server_count}. Not yet running Clients_send_pinginfo1.py.")
    except Exception as e:
        print(f"Error in check_servers_and_run: {e}")

# Get the list of hosts from the config file
try:
    hostlist = [host.strip() for host in config.get('hosts', 'hostlist').split(',')]
    print(f"Hostlist: {hostlist}")
except Exception as e:
    print(f"Error reading hostlist from config: {e}")
    sys.exit(1)

# Safely write the new server info to the config file
safe_write_config(config, client_self_name, server_name, server_info_str)

print(f"Updated config with server '{server_name}' under '{client_self_name}' with time: {final_trans_time}")

# Check if all servers have been processed and run the next step
check_servers_and_run(config, client_self_name, hostlist)

# Close the log file
log_file.close()
