import subprocess
import time
import os
import signal

def run_server():
    while True:
        # Open the log file for appending
        with open('output.log', 'a') as log_file:
            # Start the Python script with redirected output
            process = subprocess.Popen(
                ['python3', 'first_server_setup.py'],
                stdout=log_file,  # Redirect stdout to log file
                stderr=log_file   # Redirect stderr to log file
            )
        
            # Wait for 10 seconds
            time.sleep(10)
            
            # Kill the process
            os.kill(process.pid, signal.SIGTERM)
            
            # Wait another 25 seconds
            time.sleep(25)

if __name__ == "__main__":
    run_server()
