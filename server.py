import socket

server = socket.socket()
server.bind(("0.0.0.0", 5000))
server.listen()

print("Waiting...")

connection, address = server.accept()

print("Connected!")

while True:
    message = connection.recv(1024).decode()
    print(message)

    if message == "ESC":
        break

connection.close()
server.close()