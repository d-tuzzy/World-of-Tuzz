from socket import socket
from threading import Thread


def handle_client(connection: socket) -> None:
    """Handle communication with a connected client."""

    while True:
        data = connection.recv(1024) # Receive up to 1024 bytes
        message = data.decode() # Convert the bytes into text
        print(message)

        if message.endswith(": ESC"):
            break

    connection.close() # Close the client connection


def main() -> None:
    server = socket()
    server.bind(("0.0.0.0", 5000)) # Bind to port 5000 and accept connections from any device
    server.listen() # Start listening for connection

    print("Waiting...")

    while True:
        connection, address = server.accept() # Wait for a client and return its connection socket + address tuple
        print("Connected!")

        thread = Thread(
            target=handle_client, # The thread will run handle_client
            args=(connection,) # Pass the connection socket as the argument (in a single tuple)
        )
        thread.start() # The thread for this player will run independently


if __name__ == "__main__":
    main()