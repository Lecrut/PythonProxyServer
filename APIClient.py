import socket
import threading
import json
import time

from messages import *

is_client_connected = False
client_socket = None
subscribed_topics = {}
created_topics = set()
threads_lock = threading.Lock()
client_name = ""


def start(server_ip, server_port, client_id):
    global is_client_connected
    global client_socket
    global client_name

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((server_ip, server_port))

        is_client_connected = True
        client_name = client_id

        print(f'Połączono z serwerem {server_ip}:{server_port}')
        client_thread = threading.Thread(target=listen_server, args=(client_socket,))
        client_thread.start()
    except socket.error as e:
        print(f'Błąd połączenia z serwerem: {e}')
        is_client_connected = False


def listen_server(socket_client):
    global is_client_connected

    try:
        while is_client_connected:
            message = socket_client.recv(1024).decode()
            if message:
                response_message = json.loads(message)
                if response_message["type"] == "status" and response_message["topic"] == "logs":
                    status_callback(response_message["payload"])
                else:
                    topic = response_message.get("topic")
                    callback = subscribed_topics.get(topic)
                    if callback:
                        callback(response_message["payload"])
                    else:
                        print(f'Otrzymano wiadomość na niezarejestrowanym temacie: {topic}')
    except socket.error as e:
        print(f'Błąd podczas odbierania wiadomości od serwera: {e}')
        is_client_connected = False
    finally:
        socket_client.close()
        is_client_connected = False


def is_connected():
    return is_client_connected


def get_status():
    status = {
        "produced_topics": list(created_topics),
        "subscribed_topics": list(subscribed_topics.keys())
    }
    return json.dumps(status, indent=4)


def get_server_status(callback):
    status_message = client_server_status(client_name=client_name)
    send_message(status_message)


def create_producer(topic_name):
    message = client_register(client_name=client_name, topic_name=topic_name)
    send_message(message=message)
    created_topics.add(topic_name)


def produce(topic_name, payload):
    if topic_name in created_topics:
        message = client_message(client_name=client_name, topic_name=topic_name, payload=payload)
        send_message(message=message)
    else:
        print(f'Error: Not producing topic {topic_name}')


def withdraw_producer(topic_name):
    if topic_name in created_topics:
        message = client_withdraw(client_name=client_name, topic_name=topic_name)
        send_message(message=message)
        created_topics.remove(topic_name)
    else:
        print(f'Error: Not producing topic {topic_name}')


def create_subscriber(topic_name, callback):
    message = client_create_subscriber(client_name=client_name, topic_name=topic_name)
    send_message(message=message)
    subscribed_topics[topic_name] = callback


def withdraw_subscriber(topic_name):
    if topic_name in created_topics:
        message = client_withdraw_subscriber(client_name=client_name, topic_name=topic_name)
        send_message(message=message)
        del subscribed_topics[topic_name]
    else:
        print(f'Error: Not subscribed to topic {topic_name}')


def stop():
    global client_socket
    if client_socket:
        client_socket.close()

    global created_topics
    created_topics.clear()

    global subscribed_topics
    subscribed_topics.clear()

    global is_client_connected
    is_client_connected = False


def message_callback(payload):
    print(f'Callback Received message: {json.dumps(payload, indent=4)}')


def status_callback(payload):
    print(f'Callback Server status: {json.dumps(payload, indent=4)}')


def send_message(message):
    global is_client_connected

    with threads_lock:
        try:
            client_socket.sendall(json.dumps(message).encode())
        except socket.error as e:
            print(f'Error sending message: {e}')
            is_client_connected = False


if __name__ == '__main__':
    print("Client")

    while True:
        time.sleep(1)
        command = input(
            "Wprowadź komendę "
            "(start, stop, status, create_producer, produce, withdraw_producer, "
            "create_subscriber, withdraw_subscriber, server_status): ")

        switch = {
            "start": lambda: start(
                server_ip="127.0.0.1",
                server_port=12346,
                client_id=input("Wprowadź ID klienta: "))
            if not is_connected() else print("Klient jest już połączony."),
            "stop": lambda: stop(),
            "status": lambda: print(get_status()),
            "create_producer": lambda: create_producer(topic_name=input("Wprowadź nazwę tematu: ")),
            "produce": lambda: produce(input("Wprowadź nazwę tematu: "), {"content": input("Wprowadź dane: ")}),
            "withdraw_producer": lambda: withdraw_producer(topic_name=input("Wprowadź nazwę tematu: ")),
            "create_subscriber": lambda: create_subscriber(
                topic_name=input("Wprowadź nazwę tematu: "),
                callback=message_callback
            ),
            "withdraw_subscriber": lambda: withdraw_subscriber(topic_name=input("Wprowadź nazwę tematu: ")),
            "server_status": lambda: get_server_status(callback=status_callback),
            "check_connection": lambda: print("status połącznia: ", is_connected())
        }

        switch.get(command, lambda: print("Nieznana komenda. Spróbuj ponownie."))()

