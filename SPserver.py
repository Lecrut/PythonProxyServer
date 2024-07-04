import json
import socket
import threading
import time
from messages import *


topic_list_LT = {}
queue_received_topics_KKO = []
queue_to_send_topics_KKW = []
connected_clients = {}
server_socket = None


def load_json_file(file_name):
    try:
        with open(file_name, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Plik '{file_name}' nie istnieje.")
        return None


# zaczynamy nasluchiwac w serwerze
def start_tcp_listener(server_name, interface, port):
    global server_socket
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((interface, port))
        server_socket.listen(100)
        print(f"{server_name} nasłuchuje na porcie {port} na interfejsie {interface}...")

        while True:
            conn, addr = server_socket.accept()
            print(f"Nowe połączenie od {addr}")

            if conn not in connected_clients:
                connected_clients[conn] = 1

            client_thread = threading.Thread(target=handle_client, args=(conn,))
            client_thread.start()
    except socket.error as e:
        print(f"Błąd gniazda: {e}")
    finally:
        close_server()


# obsluga polaczonego klienta
def handle_client(client_socket):
    global queue_received_topics_KKO

    try:
        while True:
            mes = client_socket.recv(1024).decode()
            if not mes:
                break
            queue_received_topics_KKO.append(server_received_topics(client_socket=client_socket, message=mes))
    except socket.error as e:
        print(f"Błąd gniazda: {e}")
    finally:
        disconnect_client(client_socket=client_socket)


def close_server():
    if server_socket:
        server_socket.close()


def disconnect_client(client_socket):
    deletable_topics = []
    deletable_subscriptions = {}

    if client_socket in connected_clients:
        del connected_clients[client_socket]
    for topic, data in topic_list_LT.items():
        print(f'Aktualny temat: {topic}')
        print(data)
        client_id_to_delete = get_user_id(subscribers=data['subscribers'], socket_client=client_socket)
        if client_id_to_delete:
            del data['subscribers'][client_id_to_delete]

        for client_id, socket_client in data['subscribers'].items():
            deletable_subscriptions[client_id] = socket_client

        if client_socket in data['producers'].values():
            producers_to_remove = [producer_id for producer_id, socket in data['producers'].items() if socket == client_socket]
            for producer_id in producers_to_remove:
                del data['producers'][producer_id]

        if not data['producers']:
            deletable_topics.append(topic)
    print(deletable_subscriptions)
    print(deletable_topics)
    for topic in deletable_topics:
        del topic_list_LT[topic]
    check__deletable_users(subscriptions=deletable_subscriptions)
    client_socket.close()


def check__deletable_users(subscriptions):
    for client_id, client_socket in subscriptions.items():
        print(f'Sprawdzamy: {client_id}, {client_socket}')
        can_remove = True

        for topic, data in topic_list_LT.items():
            if client_id in data['producers']:
                can_remove = False
                break

            for sub_id, sub_sock in data['subscribers'].items():
                print(f'Subskrybent w temacie: {sub_id} ? {client_id}')
                if sub_id == client_id:
                    can_remove = False
                    break

        if can_remove:
            print(f'Do usunięcia: {client_id}, {client_socket}')
            client_socket.close()


def get_user_id(subscribers, socket_client):
    return next((client_id for client_id, client_socket in subscribers.items() if client_socket == socket_client), None)


def monitoring():
    while True:
        if queue_to_send_topics_KKW:
            item = queue_to_send_topics_KKW.pop(0)
            client_socket = item['socket']
            message = item['message']
            try:
                client_socket.sendall(json.dumps(message).encode())
                print(f'Wysłano wiadomość do klienta {connected_clients[client_socket]}: {message}')
            except socket.error as e:
                print(f'Błąd wysyłania wiadomości do klienta: {e}')

        if queue_received_topics_KKO:
            message = queue_received_topics_KKO.pop(0)
            print(f'Nastepna wiadomosc z KKO: {message}')
            if validate_message(message=message):
                handle_message(message=message['message'], client_socket=message['socket'])

        if not queue_received_topics_KKO and not queue_to_send_topics_KKW:
            time.sleep(0.001)


def handle_message(message, client_socket):
    try:
        message_data = json.loads(message)
        message_type = message_data.get('type', None)
        if message_type:
            switch_cases = {
                'register': handle_register,
                'withdraw': handle_withdraw,
                'message': handle_message_type,
                'status': handle_status,
            }
            handler = switch_cases.get(message_type)
            if handler:
                handler(message_data=message_data, client_socket=client_socket)
            else:
                print(f"Nieobsługiwany typ komunikatu: {message_type}")
        else:
            print("Nieprawidłowy format wiadomości: brak pola 'type'")
    except json.JSONDecodeError as e:
        print(f'Błąd dekodowania komunikatu JSON: {e}')
    except KeyError as e:
        print(f'Brakujące pole w komunikacie: {e}')


def process_message_data(message_data):
    topic = message_data.get('topic')
    client_id = message_data.get('id')
    mode = message_data.get('mode')
    return topic, client_id, mode


def handle_register(message_data, client_socket):
    topic, client_id, mode = process_message_data(message_data=message_data)

    if mode == 'producer':
        if topic not in topic_list_LT:
            topic_list_LT[topic] = {'producers': {}, 'subscribers': {}}
        elif client_id in topic_list_LT[topic]['producers']:
            print(f'Temat {topic} już istnieje i został utworzony przez innego producenta')
            return

        topic_list_LT[topic]['producers'][client_id] = client_socket
        connected_clients[client_socket] = client_id
        print(f'Zarejestrowano producenta {client_id} dla tematu {topic}')
    elif mode == 'subscriber':
        if client_socket in topic_list_LT[topic]['subscribers']:
            print(f'Klient już jest subskrybentem tematu {topic}')
        else:
            connected_clients[client_socket] = client_id
            topic_list_LT[topic]['subscribers'][client_id] = client_socket
            print(f'Zarejestrowano subskrybenta dla tematu {topic}')
    else:
        print(f'Nieobsługiwany tryb: {mode}')


def handle_withdraw(message_data, client_socket):
    topic, client_id, mode = process_message_data(message_data=message_data)

    if topic in topic_list_LT:
        if mode == 'producer':
            if client_id in topic_list_LT[topic]['producers'] and topic_list_LT[topic]['producers'][client_id] == client_socket:
                if not topic_list_LT[topic]['producers']:
                    del topic_list_LT[topic]
                del topic_list_LT[topic]['producers'][client_id]
                print(f'Usunięto temat {topic}')
            else:
                print(f'Klient {client_id} nie jest producentem tematu {topic}')
        elif mode == 'subscriber':
            if client_id in topic_list_LT[topic]['subscribers']:
                del topic_list_LT[topic]['subscribers'][client_id]
                print(f'Usunięto subskrypcję klienta dla tematu {topic}')
            else:
                print(f'Klient nie jest subskrybentem tematu {topic}')
        else:
            print(f'Nieobsługiwany tryb: {mode}')
    else:
        print(f'Temat {topic} nie istnieje')


def handle_message_type(message_data, client_socket):
    topic, _, _ = process_message_data(message_data=message_data)
    if topic in topic_list_LT:
        if topic_list_LT[topic]['subscribers']:
            for subscriber_socket in topic_list_LT[topic]['subscribers'].values():
                queue_to_send_topics_KKW.append(
                    server_send_topics(message_data=message_data, subscriber_socket=subscriber_socket)
                )
                print(f'Dodano komunikat do KKW dla tematu {topic}')
        else:
            print(f'Brak subskrybentów tematu {topic}')
    else:
        print(f'Temat {topic} nie istnieje')


def send_response(client_socket, message):
    response = {
        'socket': client_socket,
        'message': message
    }
    queue_to_send_topics_KKW.append(response)


def handle_status(message_data, client_socket):
    print(message_data)
    status_message = {
        "registered_topics": {},
    }
    for topic, data in topic_list_LT.items():
        status_message["registered_topics"][topic] = {
            "producers": list(data["producers"].keys()) or ["brak"],
            "subscribers": list(data["subscribers"].keys()) or ["brak"]
        }
    queue_to_send_topics_KKW.append(server_status(client_socket=client_socket, client_id=connected_clients[client_socket], status_message=status_message))
    print(queue_to_send_topics_KKW)
    print(f'Dodano status do KKW dla klienta {connected_clients[client_socket]}')


def validate_message(message):
    try:
        message_data = message['message']
        required_fields = ['type', 'id', 'topic', 'mode', 'timestamp', 'payload']
        return all(field in message_data for field in required_fields)
    except Exception as e:
        print(f'ValidateError: {e}')
        return False


def user_interface():
    while True:
        time.sleep(3)
        command = input("Wpisz komendę (np. 'show topics', 'show clients'): ")
        if command.lower() == 'show topics':
            show_registered_topics()
        if command.lower() == 'show clients':
            show_connected_clients()


def show_registered_topics():
    print("Zarejestrowane tematy:")
    for topic, data in topic_list_LT.items():
        producers = list(data['producers'].keys())
        subscribers = len(data['subscribers']) if data['subscribers'] else 0
        print(f"Temat: {topic}, Producent(ów): {producers}, Subskrybentów: {subscribers}")


def show_connected_clients():
    print("Klienci:")
    [print(f"{data}: {client}") for client, data in connected_clients.items()]


# startujemy wszystkie watki
def start_server(host, port):
    print("Server")

    data = load_json_file(file_name='config.json')

    global topic_list_LT
    topic_list_LT = {}

    global queue_received_topics_KKO
    queue_received_topics_KKO = []

    global queue_to_send_topics_KKW
    queue_to_send_topics_KKW = []

    communication_thread = threading.Thread(target=start_tcp_listener, args=(data['ServerID'], host, port))
    communication_thread.start()

    monitoring_thread = threading.Thread(target=monitoring)
    monitoring_thread.start()

    user_interface_thread = threading.Thread(target=user_interface)
    user_interface_thread.start()


if __name__ == '__main__':
    start_server(host='127.0.0.1', port=12346)
