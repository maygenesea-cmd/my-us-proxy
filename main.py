import os
import socket
import threading

# The server will automatically pick a port assigned by the US host
PROXY_HOST = '0.0.0.0'
PROXY_PORT = int(os.environ.get('PORT', 8888))
BUFFER_SIZE = 4096

def handle_client(client_socket):
    try:
        request = client_socket.recv(BUFFER_SIZE)
        if not request:
            return
        
        # Extract where the connection wants to go
        first_line = request.decode('utf-8', errors='ignore').split('\n')[0]
        url = first_line.split(' ')[1]
        
        http_pos = url.find("://")
        temp = url if http_pos == -1 else url[(http_pos + 3):]
        
        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
            
        target_host = temp[:webserver_pos] if (port_pos == -1 or webserver_pos < port_pos) else temp[:port_pos]
        target_port = 80 if (port_pos == -1 or webserver_pos < port_pos) else int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])

        # Connect out to the internet from the US server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_host, target_port))
        target_socket.sendall(request)
        
        client_socket.setblocking(False)
        target_socket.setblocking(False)
        
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if len(data) > 0: target_socket.sendall(data)
                else: break
            except BlockingIOError: pass
                
            try:
                remote_data = target_socket.recv(BUFFER_SIZE)
                if len(remote_data) > 0: client_socket.sendall(remote_data)
                else: break
            except BlockingIOError: pass
    except:
        pass
    finally:
        client_socket.close()

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(100)
    print(f"Proxy live on port {PROXY_PORT}")
    
    while True:
        client_sock, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == "__main__":
    start_proxy()
