from socket import socket

server = socket()
server.bind(("0.0.0.0", 5000)) # Bind to port 5000 and accept connections from any device
server.listen() # Start listening for connections

print("Waiting...")

connection, address = server.accept() # Wait for a client and return its connection socket + address tuple

print("Connected!")

while True:
    data = connection.recv(1024) # Receive up to 1024 bytes
    message = data.decode() # Convert the bytes into text
    print(message)

    if message == "ESC":
        break

connection.close() # Close the client connection
server.close() # Close the server socket