import datetime


def client_server_status(client_name):
    return {
        "type": "status",
        "id": client_name,
        "topic": "logs",
        "mode": "producer",
        "timestamp": datetime.datetime.now().isoformat(),
        "payload": {}
    }


def client_message(client_name, topic_name, payload):
    return {
        "type": "message",
        "id": client_name,
        "topic": topic_name,
        "mode": "producer",
        "timestamp": datetime.datetime.now().isoformat(),
        "payload": payload
    }


def client_withdraw(client_name, topic_name):
    return {
        "type": "withdraw",
        "id": client_name,
        "topic": topic_name,
        "mode": "producer",
        "timestamp": datetime.datetime.now().isoformat(),
        "payload": {}
    }


def client_create_subscriber(client_name, topic_name):
    return {
        "type": "register",
        "id": client_name,
        "topic": topic_name,
        "mode": "subscriber",
        "timestamp": datetime.datetime.now().isoformat(),
        "payload": {}
    }


def client_register(client_name, topic_name):
    return {
        "type": "register",
        "id": client_name,
        "topic": topic_name,
        "mode": "producer",
        "timestamp": datetime.datetime.now().isoformat(),
        "payload": {}
    }


def client_withdraw_subscriber(client_name, topic_name):
    return {
        "type": "withdraw",
        "id": client_name,
        "topic": topic_name,
        "mode": "subscriber",
        "timestamp": datetime.datetime.now().isoformat(),
        "payload": {}
    }


def server_status(client_socket, client_id, status_message):
    return {
        'socket': client_socket,
        'message': {
            'type': 'status',
            'id': client_id,
            'topic': 'logs',
            'mode': '',
            'timestamp': datetime.datetime.now().isoformat(),
            'payload': status_message
        }
    }


def server_received_topics(client_socket, message):
    return {
        'socket': client_socket,
        'message': message
    }


def server_send_topics(message_data, subscriber_socket):
    return {
        'socket': subscriber_socket,
        'message': message_data
    }
