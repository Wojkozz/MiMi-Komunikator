import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog
import json  # Import biblioteki JSON
import sys
import os


# Funkcja odbierająca wiadomości od serwera
def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if message.startswith("[KONTAKTY]"):
                contacts = message.split("\n", 1)[1]
                update_contacts(contacts)
            elif message.startswith("[PLIK]"):
                header = message.split(": ", 1)
                sender = header[0].replace("[PLIK] ", "")
                filename = header[1]
                file_data = client_socket.recv(65536)

                with open(f"received_{filename}", "wb") as f:
                    f.write(file_data)

                chat_history.config(state=tk.NORMAL)
                chat_history.insert(tk.END, f"{sender} przesłał plik: {filename}\n")
                chat_history.config(state=tk.DISABLED)
                chat_history.see(tk.END)
            else:
                chat_history.config(state=tk.NORMAL)
                chat_history.insert(tk.END, f"{message}\n")
                chat_history.config(state=tk.DISABLED)
                chat_history.see(tk.END)
        except Exception as e:
            print(f"Rozłączono z serwerem: {e}")
            break


# Funkcja wysyłania wiadomości
def send_message():
    message = message_entry.get()
    message = replace_emoticons(message)  # Zamiana skrótów na emotikony
    if message.strip():
        client_socket.send(message.encode("utf-8"))
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, f"Ty: {message}\n")
        chat_history.config(state=tk.DISABLED)
        message_entry.delete(0, tk.END)


# Funkcja aktualizująca listę kontaktów w GUI
def update_contacts(contacts):
    contacts_list.delete(0, tk.END)
    for contact in contacts.split("\n"):
        contacts_list.insert(tk.END, contact)


# Funkcja wysyłania prywatnych wiadomości
def send_private_message():
    selected_contact = contacts_list.get(tk.ACTIVE)
    if selected_contact:
        message = message_entry.get()
        message = replace_emoticons(message)
        if message.strip():
            private_message = f"@{selected_contact} {message}"
            client_socket.send(private_message.encode("utf-8"))
            chat_history.config(state=tk.NORMAL)
            chat_history.insert(tk.END, f"(Do {selected_contact}): {message}\n")
            chat_history.config(state=tk.DISABLED)
            message_entry.delete(0, tk.END)
    else:
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, "Wybierz kontakt, aby wysłać prywatną wiadomość.\n")
        chat_history.config(state=tk.DISABLED)


# Funkcja wysyłania plików
def send_file():
    filepath = filedialog.askopenfilename()
    if filepath:
        recipient = contacts_list.get(tk.ACTIVE)
        if not recipient:
            chat_history.config(state=tk.NORMAL)
            chat_history.insert(tk.END, "Wybierz kontakt, aby wysłać plik.\n")
            chat_history.config(state=tk.DISABLED)
            return

        filename = filepath.split("/")[-1]
        with open(filepath, "rb") as file:
            file_data = file.read()

        # Wyślij nagłówek pliku
        header = f"[PLIK]|{recipient}|{filename}"
        client_socket.send(header.encode("utf-8"))
        # Wyślij dane pliku
        client_socket.send(file_data)
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, f"Plik {filename} wysłany do {recipient}.\n")
        chat_history.config(state=tk.DISABLED)


# Funkcja zamieniająca skróty na emotikony
def replace_emoticons(message):
    for shortcut, emoji in emoticons.items():
        message = message.replace(shortcut, emoji)
    return message


# Ładowanie ustawień z pliku JSON
def load_emoticons():
    if getattr(sys, 'frozen', False):  # Jeśli aplikacja jest skompilowana (PyInstaller)
        base_path = sys._MEIPASS
    else:  # Jeśli aplikacja jest uruchamiana jako skrypt
        base_path = os.path.abspath(".")

    file_path = os.path.join(base_path, "settings.json")

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            settings = json.load(file)
            return settings.get("emoticons", {})
    except FileNotFoundError:
        print("Plik settings.json nie został znaleziony. Używam domyślnych emotikonów.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Błąd w pliku settings.json: {e}")
        return {}


# Konfiguracja połączenia z serwerem
HOST = "127.0.0.1"
PORT = 12345

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Wysłanie nazwy użytkownika
username = input("Podaj swoją nazwę użytkownika: ")
client_socket.send(username.encode("utf-8"))

# Ładowanie emotikonów z pliku JSON
emoticons = load_emoticons()

# Tworzenie GUI klienta
root = tk.Tk()
root.title(f"MiMi - {username}")
root.geometry("700x400")

# Lewa sekcja: Lista kontaktów
left_frame = tk.Frame(root, width=200, bg="#f0f0f0")
left_frame.pack(side=tk.LEFT, fill=tk.Y)

contacts_label = tk.Label(left_frame, text="Kontakty", bg="#f0f0f0", font=("Arial", 14))
contacts_label.pack(pady=10)

contacts_list = tk.Listbox(left_frame, bg="#ffffff", fg="#000000", font=("Arial", 12), height=20)
contacts_list.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

private_button = tk.Button(left_frame, text="Wyślij prywatną", bg="#007BFF", fg="white", font=("Arial", 12),
                           command=send_private_message)
private_button.pack(pady=10)

file_button = tk.Button(left_frame, text="Wyślij plik", bg="#007BFF", fg="white", font=("Arial", 12), command=send_file)
file_button.pack(pady=10)

# Prawa sekcja: Historia czatu i pole wiadomości
right_frame = tk.Frame(root, bg="#ffffff")
right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

chat_history = scrolledtext.ScrolledText(right_frame, state=tk.DISABLED, bg="#f9f9f9", font=("Arial", 12))
chat_history.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

message_entry = tk.Entry(right_frame, font=("Arial", 12))
message_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

send_button = tk.Button(right_frame, text="Wyślij", bg="#4CAF50", fg="white", font=("Arial", 12), command=send_message)
send_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Uruchamianie odbioru wiadomości w tle
threading.Thread(target=receive_messages, daemon=True).start()

# Uruchomienie GUI
root.mainloop()
