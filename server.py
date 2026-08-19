import socket

server = socket.socket()
server.bind(("0.0.0.0", 5000))
server.listen()

print("Waiting...")

connection, address = server.accept()

print("Connected!")
print(connection.recv(1024).decode())