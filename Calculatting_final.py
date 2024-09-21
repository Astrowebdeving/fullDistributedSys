import socket
import subprocess
import time
import sys
import configparser
import os
config = configparser.ConfigParser()



config.read('config1.ini')

def get_client_self_name():
    return subprocess.check_output(
        "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep $ip | awk '{print $2}'",
        shell=True, text=True
    ).strip()

client_self_name = get_client_self_name()
server_name = sys.argv[1]
trans_time1 = float(sys.argv[2])
trans_time2 = float(sys.argv[3])
trans_time3 = float(sys.argv[4])
final_trans_time = (trans_time1 + trans_time2 + trans_time3)/3

if client_self_name not in config:
    config[client_self_name] = {}

server_info_str = f'{{ "server_name": "{server_name}", "trans_time": "{final_trans_time}" }}'

def check_servers_and_run(config, client_self_name, hostlist):
    if client_self_name not in config:
        print(f"{client_self_name} not found in config.")
        return

   
    server_entries = len(config[client_self_name])


    expected_server_count = len(hostlist) - 1

    print(f"Found {server_entries} server entries for {client_self_name}. Expected: {expected_server_count}")

 
    if server_entries == expected_server_count:
        print(f"Server count matches {expected_server_count}. Running LeastTransitionSearch.py...")
        with open(f"completed_trans_calculation.txt", 'w') as f:
            f.write("True")
        time.sleep(1)
        os.system("python3 LeastTransitionSearch.py")
    else:
        print(f"Server count does not match {expected_server_count}. Not yet running LeastTransitionSearch.py.")


hostlist = [host.strip() for host in config.get('hosts', 'hostlist').split(',')]




config[client_self_name][server_name] = server_info_str

with open('config1.ini', 'w') as configfile:
    config.write(configfile)


print(f"Updated config with server '{server_name}' under '{client_self_name}' with time: {final_trans_time}")

check_servers_and_run(config, client_self_name, hostlist)


