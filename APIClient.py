import socket
import threading

is_client_connected = False


def start(server_ip, server_port, client_id):
    print(server_ip, server_port, client_id)
    global is_client_connected

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_ip, server_port))
        is_client_connected = True
        print(f'Połączono z serwerem {server_ip}:{server_port}')
    except socket.error as e:
        print(f'Błąd połączenia z serwerem: {e}')
        is_client_connected = False


def is_connected():
    return is_client_connected


def get_status():
    return "test"


def get_server_status(callback):
    print(callback)


def create_producer(topic_name):
    print(topic_name)


def produce(topic_name, payload):
    print(topic_name, payload)


def withdraw_producer(topic_name):
    print(topic_name)


def create_subscriber(topic_name, callback):
    print(topic_name, callback)


def withdraw_subscriber(topic_name):
    print(topic_name)


def stop():
    print('stop')


if __name__ == '__main__':
    print("Client")
    client_id = input("Enter client ID: ")
    start("127.0.0.1", 12345, client_id)
