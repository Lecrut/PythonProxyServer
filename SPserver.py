import json
import socket
import threading


def load_json_file(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Plik '{file_name}' nie istnieje.")
        return None


def dissconnect_client(client_socket):
    client_socket.close()


def handle_client(client_socket):
    try:
        while True:
            mes = client_socket.recv(1024).decode()
            if not mes:
                break
    except socket.error as e:
        print(f"Błąd gniazda: {e}")
    finally:
        client_socket


def start_tcp_listener(interface, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((interface, port))
        server_socket.listen(100)
        print(f"Nasłuchiwanie na porcie {port} na interfejsie {interface}...")

        while True:
            conn, addr = server_socket.accept()
            print(f"Nowe połączenie od {addr}")

            client_thread = threading.Thread(target=handle_client, args=(conn,))
            client_thread.start()
    except socket.error as e:
        print(f"Błąd gniazda: {e}")
    finally:
        server_socket.close()


def start_server(host, port):
    print("Server")
    data = load_json_file('config.json')
    threading.Thread(target=start_tcp_listener, args=(host, port)).start()


if __name__ == '__main__':
    start_server("127.0.0.1", 12345)
