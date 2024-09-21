import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ("worker1", 11434)


message = f"G;x;Startnow;x;\x04".encode('utf-8')  # \x04 is the EOT character


client_socket.sendto(message, server_address)