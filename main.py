import os
import socket
import threading

PROXY_HOST = '0.0.0.0'
PROXY_PORT = int(os.environ.get('PORT', 8888))
BUFFER_SIZE = 4096

def handle_client(client_socket):
    try:
        request = client_socket.recv(BUFFER_SIZE)
        if not request:
            return
        
        request_text = request.decode('utf-8', errors='ignore')
        lines = request_text.split('\r\n')
        
        # Parse standard proxy requests and direct host headers sent by cloud routers
        target_host = None
        target_port = 80
        
        for line in lines:
            if line.upper().startswith('HOST:'):
                host_val = line.split(':', 1)[1].strip()
                if ':' in host_val:
                    target_host, port_str = host_val.split(':', 1)
                    target_port = int(port_str)
                else:
                    target_host = host_val
                break

        # Fallback check if Host header wasn't matched cleanly
        if not target_host and len(lines) > 0:
            parts = lines[0].split(' ')
            if len(parts) > 1 and '://' in parts[1]:
                url_part = parts[1].split('://', 1)[1]
                target_host = url_part.split('/', 1)[0]
                if ':' in target_host:
                    target_host, port_str = target_host.split(':', 1)
                    target_port = int(port_str)

        # If Render is hitting our root domain directly to check if it's alive
        if not target_host or 'onrender.com' in target_host:
            client_socket.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nUS Proxy Online\n")
            return

        # Secure Handshake support (Port 443 tunneling)
        if lines[0].startswith('CONNECT'):
            target_port = 443
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((target_host, target_port))
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
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
        try:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock,)).start()
        except:
            pass

if __name__ == "__main__":
    start_proxy()
