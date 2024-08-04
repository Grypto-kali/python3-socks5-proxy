import socket
import select
import threading
import logging

USERNAME = b"user"
PASSWORD = b"pass"
PORT = 1080
LOG_CREDENTIALS = True  # Set to True to log attempted username and password on failed login

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_client(client_socket, client_address):
    try:
        logging.info(f"{client_address} Accepted connection")
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
                if LOG_CREDENTIALS:
                    logging.warning(f"{client_address} Failed login attempt with username: {username.decode()} and password: {password.decode()}")
                else:
                    logging.warning(f"{client_address} Failed login attempt with incorrect credentials")
                client_socket.sendall(b"\x01\x01")
                client_socket.close()
                return
        else:
            client_socket.sendall(b"\x05\xFF")
            client_socket.close()
            return

        handle_request(client_socket, client_address)
    except Exception as e:
        logging.error(f"{client_address} Error handling client: {e}")
        client_socket.close()

def handle_request(client_socket, client_address):
    try:
        request = client_socket.recv(4)
        mode = request[1]

        if mode == 1:  # CONNECT
            addr_type = request[3]
            if addr_type == 1:  # IPv4
                address = socket.inet_ntoa(client_socket.recv(4))
            elif addr_type == 3:  # Domain name
                domain_length = client_socket.recv(1)[0]
                address = client_socket.recv(domain_length).decode('utf-8')
            port = int.from_bytes(client_socket.recv(2), 'big')

            logging.info(f"{client_address} requested to connect to {address}:{port}")

            try:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(10)
                remote.connect((address, port))
                client_socket.sendall(b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + b"\x00\x00")
                exchange_data(client_socket, remote)
            except Exception as e:
                client_socket.sendall(b"\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00")
                logging.error(f"{client_address} Connection to remote server {address}:{port} failed: {e}")
                client_socket.close()
        else:
            client_socket.close()
    except Exception as e:
        logging.error(f"{client_address} Error handling request: {e}")
        client_socket.close()

def exchange_data(client_socket, remote_socket):
    try:
        while True:
            read_sockets, _, error_sockets = select.select([client_socket, remote_socket], [], [client_socket, remote_socket])

            if client_socket in read_sockets:
                data = client_socket.recv(4096)
                if not data:
                    break
                remote_socket.sendall(data)

            if remote_socket in read_sockets:
                data = remote_socket.recv(4096)
                if not data:
                    break
                client_socket.sendall(data)

            if client_socket in error_sockets or remote_socket in error_sockets:
                break
    except Exception as e:
        logging.error(f"Error during data exchange: {e}")
    finally:
        client_socket.close()
        remote_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    logging.info(f"Listening on port {PORT}")

    try:
        while True:
            client_socket, client_address = server.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_handler.start()
    except KeyboardInterrupt:
        logging.info("Shutting down server.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
