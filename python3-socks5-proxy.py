import socket
import select
import threading

USERNAME = b"user"
PASSWORD = b"pass"
PORT = 1080

def handle_client(client_socket):
    version, nmethods = client_socket.recv(2)
    methods = client_socket.recv(nmethods)

    if 0x02 in methods:
        client_socket.sendall(b"\x05\x02")
        version, ulen = client_socket.recv(2)
        username = client_socket.recv(ulen)
        plen = client_socket.recv(1)[0]
        password = client_socket.recv(plen)

        if username == USERNAME and password == PASSWORD:
            client_socket.sendall(b"\x01\x00")
        else:
            client_socket.sendall(b"\x01\x01")
            client_socket.close()
            return
    else:
        client_socket.sendall(b"\x05\xFF")
        client_socket.close()
        return

    request = client_socket.recv(4)
    mode = request[1]

    if mode == 1:
        addr_type = request[3]
        if addr_type == 1:
            address = socket.inet_ntoa(client_socket.recv(4))
        elif addr_type == 3:
            domain_length = client_socket.recv(1)[0]
            address = client_socket.recv(domain_length).decode('utf-8')
        port = int.from_bytes(client_socket.recv(2), 'big')

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((address, port))
            client_socket.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + b"\x00\x00")
        except Exception as e:
            client_socket.sendall(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
            client_socket.close()
            return

        exchange_data(client_socket, remote)
    else:
        client_socket.close()

def exchange_data(client_socket, remote_socket):
    while True:
        read_sockets, _, error_sockets = select.select([client_socket, remote_socket], [], [client_socket, remote_socket])

        if client_socket in read_sockets:
            data = client_socket.recv(4096)
            if not data:
                remote_socket.close()
                client_socket.close()
                break
            remote_socket.sendall(data)

        if remote_socket in read_sockets:
            data = remote_socket.recv(4096)
            if not data:
                remote_socket.close()
                client_socket.close()
                break
            client_socket.sendall(data)

        if client_socket in error_sockets or remote_socket in error_sockets:
            client_socket.close()
            remote_socket.close()
            break

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    print(f"Listening on port {PORT}")

    while True:
        client_socket, _ = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
