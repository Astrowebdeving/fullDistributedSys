import socket
import subprocess
import time
import sys
import configparser
import os
import fcntl  # For file locking
import random

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

# Function to safely write to the config file using file locking and validate entries
def safe_write_config(config, client_self_name, server_name, server_info_str):
    try:
        temp_config = f"TEST_worker_{server_name}_on_{client_self_name}.txt"
        print(f"Attempting to write to {temp_config}")  # Debugging print

        # Open the file in 'w' mode, which creates the file if it doesn't exist
        with open(temp_config, 'w') as configfile:
            fcntl.flock(configfile, fcntl.LOCK_EX)  # Acquire exclusive lock
            configfile.write(server_info_str)  # Write the data
            configfile.flush()  # Ensure buffer is flushed to disk
            fcntl.flock(configfile, fcntl.LOCK_UN)  # Release the lock

        print(f"Successfully wrote to {temp_config}")
            
       # with open('config1.ini', 'r+') as configfile:
          #  fcntl.flock(configfile, fcntl.LOCK_EX)  # Acquire exclusive lock
         #   config.read_file(configfile)  # Read the latest version of the file

            # Update the in-memory config object
        #    if client_self_name not in config:
        #        config[client_self_name] = {}

       #     config[client_self_name][server_name] = server_info_str

            # Move the file pointer to the beginning and truncate the file
      #      configfile.seek(0)
     #       configfile.truncate()

            # Write the updated config to the file
    #        config.write(configfile)

 #           # Validate that the entry was written correctly
 #           config.read('config1.ini')
 #           if server_name not in config[client_self_name]:
 #               raise ValueError(f"Entry for {server_name} was not written correctly.")

        print(f"Successfully wrote server '{server_name}' info to tempconfig.")
    except Exception as e:
        print(f"Error handling message from {server_name}: {e}")
# Function to check if all servers have been processed and run the next step
#def check_servers_and_run(config, client_self_name, hostlist):
#    try:
#        if client_self_name not in config:
##            print(f"{client_self_name} not found in config.")
#            return
#
#        server_entries = len(config[client_self_name])
#        expected_server_count = len(hostlist) - 1#

   #     print(f"Found {server_entries} server entries for {client_self_name}. Expected: {expected_server_count}")

  #      if server_entries == expected_server_count:
   #         print(f"Server count matches {expected_server_count}. Running Clients_send_pinginfo1.py...")
   #         with open(f"completed_trans_calculation.txt", 'w') as f:
   #             f.write("True")
   #         time.sleep(1)
    #        try:
    #            os.system("python3 Clients_send_pinginfo1.py > output4.log 2>&1 &")
    #        except Exception as e:
    #            print(f"Error in server loop: {e}")
    #    else:
    #        print(f"Server count does not match {expected_server_count}. Not yet running Clients_send_pinginfo1.py.")
   # except Exception as e:
     #   print(f"Error in check_servers_and_run: {e}")

def is_process_running(process_name):
    """Check if a process with the given name is running."""
    try:
        # Use pgrep to check if the process is running
        result = subprocess.run(['pgrep', '-f', process_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:  # 0 means the process was found
            return True
        return False
    except Exception as e:
        print(f"Error checking for running process: {e}")
        return False

def monitor_and_update_config(client_self_name, config):
    # Get hostlist and calculate expected server count
    hostlist = [host.strip() for host in config.get('hosts', 'hostlist').split(',')]
    expected_server_count = len(hostlist) - 1

    # Dictionary to store detected file content
    monitored_files = {}

    # Check for the required files starting with "Test_worker"
    for filename in os.listdir("."):
        if filename.startswith("TEST_worker") and filename.endswith(".txt"):
            if filename not in monitored_files and os.path.exists(filename):
                try:
                    # Open the file and read its content
                    with open(filename, 'r') as f:
                        content = f.read().strip()
                        if content:  # Only consider non-empty files
                            monitored_files[filename] = content
                            print(f"Detected and read content from {filename}")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    # If the number of detected files does not match the expected count, exit
    sleep_time = random.uniform(0, 0.5)

# Sleep for the random amount of time
    time.sleep(sleep_time)
    if len(monitored_files) != expected_server_count:
        print(f"Expected {expected_server_count} files, but only found {len(monitored_files)}.")
        
        sys.exit(1)

    # All expected files have been detected, now write to config1.ini
    try:
        with open('config1.ini', 'r+') as configfile:
            fcntl.flock(configfile, fcntl.LOCK_EX)  # Acquire exclusive lock
            config.read_file(configfile)  # Reload the config file
            
            # Ensure the client_self_name section exists
            if client_self_name not in config:
                config[client_self_name] = {}

            # Update config with the content of each monitored file
            for filename, content in monitored_files.items():
                server_name = filename.split("_")[2]  # Extract server_name from file name
                config[client_self_name][server_name] = content

            # Move file pointer to the beginning and truncate the file
            configfile.seek(0)
            configfile.truncate()

            # Write the updated config to the file
            config.write(configfile)
            fcntl.flock(configfile, fcntl.LOCK_UN)  # Release the lock

        print(f"Updated config1.ini with data from worker files under section [{client_self_name}]")
    except Exception as e:
        print(f"Error while writing to config1.ini: {e}")
        sys.exit(1)

    # Check if Clients_send_pinginfo1.py is already running
    if is_process_running("Clients_send_pinginfo1.py"):
        print("Clients_send_pinginfo1.py is already running. Exiting without starting a new instance.")
        sys.exit(0)

    # Run the next script if not already running
    try:
        print("Triggering Clients_send_pinginfo1.py...")
        os.system("python3 Clients_send_pinginfo1.py > output4.log 2>&1 &")
    except Exception as e:
        print(f"Error running Clients_send_pinginfo1.py: {e}")
        sys.exit(1)

    # Delete the monitored files after the script is executed
    try:
        for filename in monitored_files.keys():
            os.remove(filename)
            print(f"Deleted {filename}")
    except Exception as e:
        print(f"Error deleting files: {e}")
        sys.exit(1)
# Get the list of hosts from the config file
try:
    hostlist = [host.strip() for host in config.get('hosts', 'hostlist').split(',')]
    print(f"Hostlist: {hostlist}")
except Exception as e:
    print(f"Error reading hostlist from config: {e}")
    sys.exit(1)

# Safely write the new server info to the config file
safe_write_config(config, client_self_name, server_name, f'{{ "server_name": "{server_name}", "trans_time": "{final_trans_time}" }}')

print(f"Updated config with server '{server_name}' under '{client_self_name}' with time: {final_trans_time}")

# Check if all servers have been processed and run the next step
monitor_and_update_config(client_self_name, config)
#check_servers_and_run(config, client_self_name, hostlist)

# Close the log file
log_file.close()
