import socket
import threading

# Konfiguracja serwera
HOST = "127.0.0.1"
PORT = 12345

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

clients = {}  # Słownik {adres klienta: gniazdo}
usernames = {}  # Słownik {gniazdo: nazwa użytkownika}

# Funkcja obsługująca indywidualnych klientów
def handle_client(client_socket):
    username = client_socket.recv(1024).decode("utf-8")
    usernames[client_socket] = username
    broadcast(f"[{username}] dołączył do czatu.", client_socket)
    update_contacts()

    try:
        while True:
            message = client_socket.recv(1024).decode("utf-8")

            if message.startswith("[PLIK]|"):  # Obsługa przesyłania plików
                handle_file_transfer(client_socket, message)
            elif message.startswith("@"):  # Prywatna wiadomość
                handle_private_message(client_socket, message)
            else:  # Wiadomość ogólna
                broadcast(f"[{username}] {message}", client_socket)
    except:
        # Odłącz klienta w razie błędu
        disconnect_client(client_socket)

# Funkcja obsługująca przesyłanie plików
def handle_file_transfer(client_socket, message):
    _, recipient, filename = message.split("|")
    file_data = client_socket.recv(65536)

    recipient_socket = find_client_by_username(recipient)
    if recipient_socket:
        recipient_socket.send(f"[PLIK] {usernames[client_socket]}: {filename}".encode("utf-8"))
        recipient_socket.send(file_data)

# Funkcja obsługująca prywatne wiadomości
def handle_private_message(client_socket, message):
    target_username, private_message = message[1:].split(" ", 1)
    recipient_socket = find_client_by_username(target_username)
    if recipient_socket:
        sender = usernames[client_socket]
        recipient_socket.send(f"(Prywatna wiadomość od {sender}): {private_message}".encode("utf-8"))
    else:
        client_socket.send("Nie znaleziono użytkownika.\n".encode("utf-8"))

# Funkcja wysyłająca wiadomości do wszystkich klientów
def broadcast(message, sender_socket=None):
    for client in clients.values():
        if client != sender_socket:
            try:
                client.send(message.encode("utf-8"))
            except:
                disconnect_client(client)

# Funkcja aktualizująca listę kontaktów
def update_contacts():
    contacts = "\n".join(usernames.values())
    for client in clients.values():
        try:
            client.send(f"[KONTAKTY]\n{contacts}".encode("utf-8"))
        except:
            disconnect_client(client)

# Funkcja znajdowania klienta po nazwie użytkownika
def find_client_by_username(username):
    for client, name in usernames.items():
        if name == username:
            return client
    return None

# Funkcja odłączająca klienta
def disconnect_client(client_socket):
    if client_socket in usernames:
        username = usernames[client_socket]
        broadcast(f"[{username}] opuścił czat.", client_socket)
        del usernames[client_socket]
    if client_socket in clients.values():
        for addr, client in list(clients.items()):
            if client == client_socket:
                del clients[addr]
                break
    update_contacts()
    client_socket.close()

# Funkcja akceptująca nowych klientów
def accept_clients():
    print("Serwer nasłuchuje...")
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Nowe połączenie: {client_address}")
        clients[client_address] = client_socket
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

# Uruchomienie serwera
accept_clients()
