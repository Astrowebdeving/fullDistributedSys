import socket
import subprocess
import multiprocessing

# Function to get the server's self name based on IP address
def get_server_self_name():
    return subprocess.check_output(
        "ip=$(hostname -I | awk '{print $1}')\n cat /etc/hosts | grep -w $ip | awk '{print $2}'",
        shell=True, text=True
    ).strip()

# Function to handle client requests
def handle_client(data, address):
    try:
        message = data.decode('utf-8')
        
        if message.endswith('\x04'):
            message = message[:-1]  # Remove the special character

            if message.startswith("T1"):
                parts = message.split(';')
                repetition_index = int(parts[4])
                
                # Process the message

                # Send the response back to the client
                response_message = f"T2;x;{server_self_name};z*;{repetition_index}".encode('utf-8')
                response_socket.sendto(response_message, (address[0], 13898))
                print(f"Processing and sent back message from {address[0]}, 13898 on , repetition {repetition_index}")

    except Exception as e:
        print(f"Error handling message from {address}: {e}")

# Main server function to listen for incoming messages and start new processes
def server_process():
    # Create the server socket to listen for incoming messages
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', 13897))

    # Create a socket for sending responses
    global response_socket
    response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            # Receive data and client address (IP, port)
            data, address = server_socket.recvfrom(1024)
            
            # Start a new process to handle the client's request
            multiprocessing.Process(target=handle_client, args=(data, address)).start()

        except Exception as e:
            print(f"Error in server loop: {e}")

# Start the server with multiprocessing
if __name__ == '__main__':
    server_self_name = get_server_self_name()

    # Start the server process
    server_process()
